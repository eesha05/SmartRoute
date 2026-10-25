
import math
import pandas as pd
import streamlit as st

# -------------------------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------------------------
st.set_page_config(
    page_title="SmartRoute | Traffic Game Theory",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 SmartRoute")
st.subheader(
    "Game-Theoretic Modelling of Traffic Route Selection in Smart Cities"
)

st.write(
    "Simulate how drivers choose between two routes, "
    "find Nash equilibrium, and compare it with the "
    "socially optimal traffic allocation."
)

# -------------------------------------------------
# 2. INPUTS
# -------------------------------------------------
st.sidebar.header("Traffic Simulation Settings")

N = st.sidebar.slider(
    "Total number of vehicles",
    min_value=10,
    max_value=500,
    value=100,
    step=10
)

st.sidebar.subheader("Route A")

a_A = st.sidebar.number_input(
    "Route A: free-flow time (minutes)",
    min_value=1.0,
    max_value=100.0,
    value=10.0,
    step=1.0
)

b_A = st.sidebar.number_input(
    "Route A: congestion coefficient",
    min_value=0.0,
    max_value=2.0,
    value=0.20,
    step=0.01,
    format="%.2f"
)

st.sidebar.subheader("Route B")

a_B = st.sidebar.number_input(
    "Route B: free-flow time (minutes)",
    min_value=1.0,
    max_value=100.0,
    value=15.0,
    step=1.0
)

b_B = st.sidebar.number_input(
    "Route B: congestion coefficient",
    min_value=0.0,
    max_value=2.0,
    value=0.05,
    step=0.01,
    format="%.2f"
)

initial_share_A = st.sidebar.slider(
    "Initial percentage of vehicles on Route A",
    min_value=0,
    max_value=100,
    value=100,
    step=5
)

st.sidebar.caption(
    "The model assumes two parallel routes, fixed demand, "
    "and travel time increasing linearly with traffic."
)

# -------------------------------------------------
# 3. TRAVEL-TIME AND COST FUNCTIONS
# -------------------------------------------------
def route_A_time(n_A):
    return a_A + b_A * n_A


def route_B_time(n_B):
    return a_B + b_B * n_B


def calculate_metrics(n_A):
    """Calculate the results for a traffic allocation."""
    n_B = N - n_A

    time_A = route_A_time(n_A)
    time_B = route_B_time(n_B)

    total_time = n_A * time_A + n_B * time_B

    average_time = total_time / N

    return {
        "Vehicles on Route A": n_A,
        "Vehicles on Route B": n_B,
        "Route A time (min)": time_A,
        "Route B time (min)": time_B,
        "Total travel time (vehicle-min)": total_time,
        "Average travel time (min)": average_time
    }


# -------------------------------------------------
# 4. NASH EQUILIBRIUM CHECK
# -------------------------------------------------
def is_nash_equilibrium(n_A):
    """
    Check whether any single driver can reduce their
    travel time by switching routes.

    Drivers on A compare their current cost with the
    cost of entering B.

    Drivers on B compare their current cost with the
    cost of entering A.
    """
    n_B = N - n_A
    current_A = route_A_time(n_A)
    current_B = route_B_time(n_B)

    # If A has drivers, none should benefit from moving to B.
    if n_A > 0:
        cost_after_A_to_B = route_B_time(n_B + 1)

        if current_A > cost_after_A_to_B + 1e-9:
            return False

    # If B has drivers, none should benefit from moving to A.
    if n_B > 0:
        cost_after_B_to_A = route_A_time(n_A + 1)

        if current_B > cost_after_B_to_A + 1e-9:
            return False

    return True


# -------------------------------------------------
# 5. EVALUATE EVERY POSSIBLE ALLOCATION
# -------------------------------------------------
all_results = []

for vehicles_A in range(N + 1):
    result = calculate_metrics(vehicles_A)
    result["Nash equilibrium"] = is_nash_equilibrium(
        vehicles_A
    )
    all_results.append(result)

results_df = pd.DataFrame(all_results)

# There can be one or multiple Nash equilibria.
nash_df = results_df[results_df["Nash equilibrium"]].copy()

# Find the minimum possible total travel time.
minimum_total = results_df[
    "Total travel time (vehicle-min)"
].min()

social_df = results_df[
    results_df["Total travel time (vehicle-min)"]
    .apply(lambda x: math.isclose(
        x, minimum_total, rel_tol=1e-9, abs_tol=1e-8
    ))
].copy()

# Select the lowest-total-cost Nash equilibrium for
# the side-by-side comparison, if multiple exist.
selected_nash = nash_df.sort_values(
    "Total travel time (vehicle-min)"
).iloc[0]

selected_social = social_df.iloc[0]

# -------------------------------------------------
# 6. INITIAL TRAFFIC ALLOCATION
# -------------------------------------------------
initial_A = round(N * initial_share_A / 100)
initial_result = calculate_metrics(initial_A)

nash_result = selected_nash.to_dict()
social_result = selected_social.to_dict()

# -------------------------------------------------
# 7. SUMMARY METRICS
# -------------------------------------------------
st.header("Simulation Results")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total vehicles",
    N
)

col2.metric(
    "Nash: vehicles on A",
    int(nash_result["Vehicles on Route A"])
)

col3.metric(
    "Optimum: vehicles on A",
    int(social_result["Vehicles on Route A"])
)

col4.metric(
    "Minimum total travel time",
    f"{minimum_total:,.2f} vehicle-min"
)

st.info(
    f"Found {len(nash_df)} pure Nash equilibrium "
    f"allocation(s) among the {N + 1} possible allocations."
)

# -------------------------------------------------
# 8. ROUTE DISTRIBUTION COMPARISON
# -------------------------------------------------
st.header("1. Vehicle Distribution")

allocation_df = pd.DataFrame([
    {
        "Scenario": "Initial",
        "Route A": initial_result["Vehicles on Route A"],
        "Route B": initial_result["Vehicles on Route B"]
    },
    {
        "Scenario": "Nash equilibrium",
        "Route A": int(nash_result["Vehicles on Route A"]),
        "Route B": int(nash_result["Vehicles on Route B"])
    },
    {
        "Scenario": "Social optimum",
        "Route A": int(social_result["Vehicles on Route A"]),
        "Route B": int(social_result["Vehicles on Route B"])
    }
])

st.bar_chart(
    allocation_df.set_index("Scenario"),
    y=["Route A", "Route B"]
)

st.dataframe(allocation_df,)

# -------------------------------------------------
# 9. TRAVEL TIME COMPARISON
# -------------------------------------------------
st.header("2. Travel Time Comparison")

time_df = pd.DataFrame([
    {
        "Scenario": "Initial",
        "Route A time": initial_result["Route A time (min)"],
        "Route B time": initial_result["Route B time (min)"],
        "Average time": initial_result["Average travel time (min)"]
    },
    {
        "Scenario": "Nash equilibrium",
        "Route A time": nash_result["Route A time (min)"],
        "Route B time": nash_result["Route B time (min)"],
        "Average time": nash_result["Average travel time (min)"]
    },
    {
        "Scenario": "Social optimum",
        "Route A time": social_result["Route A time (min)"],
        "Route B time": social_result["Route B time (min)"],
        "Average time": social_result["Average travel time (min)"]
    }
])

st.bar_chart(
    time_df.set_index("Scenario"),
    y=["Route A time", "Route B time"]
)

st.dataframe(
    time_df.round(2)
)

# -------------------------------------------------
# 10. TOTAL TRAVEL TIME FOR EVERY ALLOCATION
# -------------------------------------------------
st.header("3. Total Travel Time vs Route Allocation")

curve_df = results_df[
    ["Vehicles on Route A", "Total travel time (vehicle-min)"]
].set_index("Vehicles on Route A")

st.line_chart(curve_df)

st.caption(
    "The lowest point on this curve represents the "
    "socially optimal allocation."
)

# -------------------------------------------------
# 11. NASH EQUILIBRIUM DETAILS
# -------------------------------------------------
st.header("4. Nash Equilibrium Analysis")

st.write(
    "A Nash equilibrium occurs when no individual driver "
    "can improve their travel time by switching routes alone."
)

nash_display = nash_df[
    [
        "Vehicles on Route A",
        "Vehicles on Route B",
        "Route A time (min)",
        "Route B time (min)",
        "Total travel time (vehicle-min)"
    ]
].round(2)

st.dataframe(
    nash_display
)

st.success(
    "The equilibrium check compares the current travel time "
    "of a driver with the travel time after a unilateral switch, "
    "including the effect of entering the other route."
)

# ---------------- PAYOFF MATRIX ----------------

st.header("Payoff Matrix: Route Selection Game")

st.write(
    "Two drivers choose between Route A and Route B. "
    "Each payoff is the negative of that driver's travel time, "
    "so a higher payoff means a shorter travel time."
)

st.write(
    "**Assumption:** There are 100 drivers in total. "
    "The other 98 drivers are split equally: 49 on each route."
)

payoff_matrix = pd.DataFrame(
    [
        ["(-20.20, -20.20)", "(-20.00, -17.50)"],
        ["(-17.50, -20.00)", "(-17.55, -17.55)"]
    ],
    index=["Route A", "Route B"],
    columns=["Driver 2: Route A", "Driver 2: Route B"]
)

payoff_matrix.index.name = "Driver 1"

st.table(payoff_matrix)

st.caption(
    "Each cell represents (Driver 1 payoff, Driver 2 payoff), "
    "measured in negative travel-time minutes."
)

st.subheader("How to interpret the matrix")

st.markdown("""
- **Both choose Route A:** Each experiences 20.2 minutes.
- **Driver 1 chooses A, Driver 2 chooses B:** Their travel times are 20 and 17.5 minutes.
- **Driver 1 chooses B, Driver 2 chooses A:** Their travel times are 17.5 and 20 minutes.
- **Both choose Route B:** Each experiences 17.55 minutes.

The Nash equilibrium is the outcome where neither driver can
improve their own travel time by switching routes alone.
""")


# -------------------------------------------------
# 12. SOCIAL OPTIMUM DETAILS
# -------------------------------------------------
st.header("5. Social Optimum Analysis")

st.write(
    "The social optimum minimizes the sum of the travel times "
    "of all vehicles, rather than optimizing one driver's decision."
)

social_display = social_df[
    [
        "Vehicles on Route A",
        "Vehicles on Route B",
        "Route A time (min)",
        "Route B time (min)",
        "Total travel time (vehicle-min)"
    ]
].round(2)

st.dataframe(
    social_display
)

nash_total = nash_result["Total travel time (vehicle-min)"]
social_total = social_result["Total travel time (vehicle-min)"]

difference = nash_total - social_total

st.metric(
    "Nash total minus optimal total",
    f"{difference:,.2f} vehicle-min"
)

if social_total > 0:
    inefficiency_percent = (
        difference / social_total
    ) * 100

    st.write(
        f"Relative increase over the social optimum: "
        f"{inefficiency_percent:.2f}%."
    )

# ------------ DOMINANCE AND MIXED STRATEGIES ------------

st.header("Dominance Analysis")

st.write(
    "Compare each driver's payoffs for Route A and Route B "
    "against both possible choices of the other driver."
)

# Payoffs are negative travel times.
# Rows: Driver 1's action (A, B)
# Columns: Driver 2's action (A, B)
#
# This matrix is illustrative; these values should match
# the payoff matrix displayed earlier in the dashboard.

A = [-20.20, -20.00]  # Driver 1 chooses A
B = [-17.50, -17.55]  # Driver 1 chooses B

a_better = all(a > b for a, b in zip(A, B))
b_better = all(b > a for a, b in zip(A, B))

if a_better:
    st.success("Route A strictly dominates Route B for Driver 1.")
elif b_better:
    st.success("Route B strictly dominates Route A for Driver 1.")
else:
    st.info(
        "Neither route strictly dominates the other for Driver 1. "
        "The better choice depends on Driver 2's action."
    )




# -------------------------------------------------
# 13. ALLOCATION TABLE
# -------------------------------------------------
with st.expander("View every possible allocation"):
    st.dataframe(
        results_df.round(3)
    )

# -------------------------------------------------
# 14. ASSUMPTIONS AND CONCLUSION
# -------------------------------------------------
st.header("6. Model Assumptions")

st.markdown("""
- There are two routes connecting the same origin and destination.
- The total number of vehicles remains fixed.
- Each vehicle chooses the route with the lower travel time.
- Travel time increases linearly with the number of vehicles.
- A single driver changing routes changes the destination
  route's traffic count by one.
- All drivers have the same objective and know the cost functions.
- This is a simplified model, not a live traffic prediction system.
""")

st.header("Conclusion")

st.write(
    "SmartRoute compares individual driver decisions with "
    "system-wide traffic optimization. The results illustrate "
    "how route choices, congestion, Nash equilibrium, and "
    "social welfare are connected in smart-city traffic planning."
)
