"""
SEIR Epidemiological Model v2: Multi-Pathogen Surveillance & Counterfactual Engine
-----------------------------------------------------------------------------------
Extends standard SEIR mechanics to support multi-contagion profiling (COVID-19 variants, 
Seasonal Flu, Measles, Mpox, Disease X), clinical hospital burden estimation, and 
policy counterfactual simulations across interconnected NY/NJ regions.
"""

from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import matplotlib.pyplot as plt


@dataclass
class PathogenProfile:
    """Configuration container for specific pathogen biological and clinical parameters."""
    name: str
    R0: float
    incubation_days: float   # 1 / sigma
    infectious_days: float   # 1 / gamma
    ed_visit_rate: float     # Estimated % of infectious cases visiting Emergency Dept
    hospitalization_rate: float # Estimated % requiring inpatient hospitalization
    description: str

    @property
    def sigma(self) -> float:
        """Incubation rate (1 / days)."""
        return 1.0 / self.incubation_days

    @property
    def gamma(self) -> float:
        """Recovery rate (1 / days)."""
        return 1.0 / self.infectious_days

    @property
    def beta(self) -> float:
        """Transmission rate parameter (beta = R0 * gamma)."""
        return self.R0 * self.gamma


# Pre-defined biological parameter profiles for major contagions
PATHOGEN_PROFILES = {
    'covid19_omicron': PathogenProfile(
        name='COVID-19 (Omicron Variant)',
        R0=3.5,
        incubation_days=3.0,
        infectious_days=5.0,
        ed_visit_rate=0.025,
        hospitalization_rate=0.012,
        description='Highly transmissible respiratory variant with shorter incubation and lower severity rate.'
    ),
    'covid19_wildtype': PathogenProfile(
        name='COVID-19 (Ancestral Strain)',
        R0=2.5,
        incubation_days=5.2,
        infectious_days=7.0,
        ed_visit_rate=0.050,
        hospitalization_rate=0.025,
        description='Baseline SARS-CoV-2 strain with moderate incubation and clinical severity.'
    ),
    'seasonal_flu': PathogenProfile(
        name='Seasonal Influenza (H1N1/H3N2)',
        R0=1.3,
        incubation_days=2.0,
        infectious_days=4.0,
        ed_visit_rate=0.018,
        hospitalization_rate=0.008,
        description='Rapid onset respiratory infection with low-to-moderate R0 and quick recovery.'
    ),
    'measles': PathogenProfile(
        name='Measles Virus',
        R0=15.0,
        incubation_days=11.0,
        infectious_days=8.0,
        ed_visit_rate=0.120,
        hospitalization_rate=0.060,
        description='Extremely infectious airborne virus requiring high herd immunity thresholds (>92%).'
    ),
    'mpox': PathogenProfile(
        name='Mpox Virus (Clade II)',
        R0=1.8,
        incubation_days=8.5,
        infectious_days=14.0,
        ed_visit_rate=0.040,
        hospitalization_rate=0.010,
        description='Slower transmission velocity with long incubation and prolonged infectious duration.'
    ),
    'disease_x': PathogenProfile(
        name='Emerging Pathogen (Disease X)',
        R0=4.0,
        incubation_days=4.0,
        infectious_days=6.0,
        ed_visit_rate=0.060,
        hospitalization_rate=0.030,
        description='Generic template for testing novel pandemic surge scenarios.'
    )
}


class SEIRModel:
    """
    Single-Population SEIR Model supporting multi-pathogen profiling and clinical estimation.
    """
    def __init__(self, population: float, beta: float, sigma: float, gamma: float, pathogen_name: str = "Custom"):
        self.N = population
        self.beta = beta
        self.sigma = sigma
        self.gamma = gamma
        self.pathogen_name = pathogen_name

    @classmethod
    def from_pathogen(cls, pathogen_key: str, population: float, beta_override: float = None):
        """
        Instantiates an SEIRModel initialized with pre-defined pathogen biology.
        """
        if pathogen_key not in PATHOGEN_PROFILES:
            raise ValueError(f"Unknown pathogen '{pathogen_key}'. Options: {list(PATHOGEN_PROFILES.keys())}")
        
        profile = PATHOGEN_PROFILES[pathogen_key]
        beta = beta_override if beta_override is not None else profile.beta
        return cls(
            population=population,
            beta=beta,
            sigma=profile.sigma,
            gamma=profile.gamma,
            pathogen_name=profile.name
        )

    @property
    def R0(self) -> float:
        return self.beta / self.gamma

    def _ode_system(self, t, y, beta_func=None):
        S, E, I, R = y
        beta = beta_func(t) if beta_func is not None else self.beta
        
        dSdt = - (beta * S * I) / self.N
        dEdt = (beta * S * I) / self.N - self.sigma * E
        dIdt = self.sigma * E - self.gamma * I
        dRdt = self.gamma * I
        
        return [dSdt, dEdt, dIdt, dRdt]

    def simulate(self, initial_cases: float, days: int, initial_exposed: float = 0.0, beta_func=None, pathogen_key: str = None):
        """
        Simulates SEIR trajectory, calculating R_t, inflection acceleration, and clinical burden.
        """
        I0 = initial_cases
        E0 = initial_exposed
        R0_comp = 0.0
        S0 = self.N - E0 - I0 - R0_comp

        y0 = [S0, E0, I0, R0_comp]
        t_span = (0, days)
        t_eval = np.linspace(0, days, days + 1)

        solution = solve_ivp(
            fun=lambda t, y: self._ode_system(t, y, beta_func=beta_func),
            t_span=t_span,
            y0=y0,
            t_eval=t_eval,
            method='RK45'
        )

        S, E, I, R = solution.y
        
        # Effective Reproduction Number R_t over time
        beta_t = np.array([beta_func(t) if beta_func is not None else self.beta for t in solution.t])
        R_t = (beta_t / self.gamma) * (S / self.N)

        # Acceleration and inflection day
        dIdt = np.gradient(I, solution.t)
        inflection_day = solution.t[np.argmax(dIdt)]

        # Clinical projections if pathogen profile provided
        ed_visits = None
        hospitalizations = None
        if pathogen_key and pathogen_key in PATHOGEN_PROFILES:
            prof = PATHOGEN_PROFILES[pathogen_key]
            ed_visits = I * prof.ed_visit_rate
            hospitalizations = I * prof.hospitalization_rate

        return {
            't': solution.t,
            'S': S,
            'E': E,
            'I': I,
            'R': R,
            'R_t': R_t,
            'dIdt': dIdt,
            'inflection_day': inflection_day,
            'peak_infectious_day': solution.t[np.argmax(I)],
            'peak_infectious_count': np.max(I),
            'ed_visits': ed_visits,
            'hospitalizations': hospitalizations
        }


class SpatialSEIRModel:
    """
    Multi-Patch Spatial SEIR Model coupled by a commuter mobility matrix W_ij.
    Supports counterfactual scenario modeling (e.g., travel reductions or mask mandates).
    """
    def __init__(self, populations: np.ndarray, betas: np.ndarray, sigma: float, gamma: float, mobility_matrix: np.ndarray):
        self.num_patches = len(populations)
        self.N = populations
        self.betas = betas
        self.sigma = sigma
        self.gamma = gamma
        self.M = mobility_matrix

    @classmethod
    def from_pathogen(cls, pathogen_key: str, populations: np.ndarray, mobility_matrix: np.ndarray, beta_multiplier: float = 1.0):
        """Builds a spatial SEIR model from a pre-configured pathogen profile."""
        if pathogen_key not in PATHOGEN_PROFILES:
            raise ValueError(f"Unknown pathogen '{pathogen_key}'.")
        prof = PATHOGEN_PROFILES[pathogen_key]
        betas = np.full(len(populations), prof.beta * beta_multiplier)
        return cls(
            populations=populations,
            betas=betas,
            sigma=prof.sigma,
            gamma=prof.gamma,
            mobility_matrix=mobility_matrix
        )

    def _ode_system(self, t, y, M_override=None, betas_override=None):
        S = y[0:self.num_patches]
        E = y[self.num_patches:2*self.num_patches]
        I = y[2*self.num_patches:3*self.num_patches]
        R = y[3*self.num_patches:4*self.num_patches]

        M = M_override if M_override is not None else self.M
        betas = betas_override if betas_override is not None else self.betas

        effective_I = I + np.dot(M.T, I)
        
        dSdt = - (betas * S * effective_I) / self.N
        dEdt = (betas * S * effective_I) / self.N - self.sigma * E
        dIdt = self.sigma * E - self.gamma * I
        dRdt = self.gamma * I

        return np.concatenate([dSdt, dEdt, dIdt, dRdt])

    def simulate(self, initial_cases: np.ndarray, days: int):
        I0 = initial_cases
        E0 = np.zeros(self.num_patches)
        R0_comp = np.zeros(self.num_patches)
        S0 = self.N - I0

        y0 = np.concatenate([S0, E0, I0, R0_comp])
        t_span = (0, days)
        t_eval = np.linspace(0, days, days + 1)

        solution = solve_ivp(
            fun=self._ode_system,
            t_span=t_span,
            y0=y0,
            t_eval=t_eval,
            method='RK45'
        )

        S_spatial = solution.y[0:self.num_patches, :]
        E_spatial = solution.y[self.num_patches:2*self.num_patches, :]
        I_spatial = solution.y[2*self.num_patches:3*self.num_patches, :]
        R_spatial = solution.y[3*self.num_patches:4*self.num_patches, :]

        return {
            't': solution.t,
            'S': S_spatial,
            'E': E_spatial,
            'I': I_spatial,
            'R': R_spatial
        }

    def simulate_counterfactual(self, initial_cases: np.ndarray, days: int, mobility_reduction_pct: float = 0.0, transmission_reduction_pct: float = 0.0):
        """
        Runs baseline vs. policy counterfactual simulation.
        
        Parameters:
            mobility_reduction_pct (float): % reduction in cross-border commuter flows (0.0 to 1.0)
            transmission_reduction_pct (float): % reduction in local contact rate/transmission (0.0 to 1.0)
        """
        # Baseline simulation
        baseline_res = self.simulate(initial_cases, days)

        # Adjusted parameters for intervention scenario
        adjusted_M = self.M * (1.0 - mobility_reduction_pct)
        adjusted_betas = self.betas * (1.0 - transmission_reduction_pct)

        y0 = np.concatenate([self.N - initial_cases, np.zeros(self.num_patches), initial_cases, np.zeros(self.num_patches)])
        t_span = (0, days)
        t_eval = np.linspace(0, days, days + 1)

        sol_cf = solve_ivp(
            fun=lambda t, y: self._ode_system(t, y, M_override=adjusted_M, betas_override=adjusted_betas),
            t_span=t_span,
            y0=y0,
            t_eval=t_eval,
            method='RK45'
        )

        I_counterfactual = sol_cf.y[2*self.num_patches:3*self.num_patches, :]

        return {
            't': sol_cf.t,
            'baseline_I': baseline_res['I'],
            'counterfactual_I': I_counterfactual,
            'cases_averted_total': np.sum(baseline_res['I']) - np.sum(I_counterfactual)
        }


def compare_pathogens(population: float = 50000, initial_cases: float = 10, days: int = 90):
    """
    Utility function to run and compare simulation trajectories across multiple pathogens.
    """
    results = {}
    for key, prof in PATHOGEN_PROFILES.items():
        model = SEIRModel.from_pathogen(key, population=population)
        sim = model.simulate(initial_cases=initial_cases, days=days, pathogen_key=key)
        results[key] = {
            'profile': prof,
            'simulation': sim
        }
    return results


if __name__ == '__main__':
    print("--- Multi-Pathogen SEIR Engine Demonstration ---")
    
    # 1. Compare trajectories across COVID-19, Seasonal Flu, and Measles
    comp = compare_pathogens(population=50000, initial_cases=10, days=90)
    
    for key, data in comp.items():
        prof = data['profile']
        sim = data['simulation']
        print(f"\nPathogen: {prof.name}")
        print(f" - R0: {prof.R0:.1f} | Incubation: {prof.incubation_days:.1f} days | Infectious: {prof.infectious_days:.1f} days")
        print(f" - Peak Infectious Day: Day {sim['peak_infectious_day']:.0f}")
        print(f" - Peak Infectious Count: {sim['peak_infectious_count']:.0f} cases")
        print(f" - Peak Acceleration (Inflection Day): Day {sim['inflection_day']:.0f}")
        if sim['ed_visits'] is not None:
            print(f" - Projected Peak ED Visit Demand: {np.max(sim['ed_visits']):.0f} visits/day")

    print("\n--- Multi-Pathogen Engine Executed Successfully ---")
