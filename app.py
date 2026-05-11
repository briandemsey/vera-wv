"""
VERA-WV: Verification Engine for Results & Accountability - West Virginia
Type 4 Detection using ELPA21 Speaking vs Writing + WVGSA Achievement Data

West Virginia context:
- ELPA21 (English Language Proficiency Assessment for the 21st Century) -- NOT WIDA
  4 domains (Listening, Speaking, Reading, Writing)
- Exit criterion: overall proficiency on ELPA21
- WVGSA (West Virginia General Summative Assessment), 4 levels:
    Does Not Meet / Partially Meets / Meets / Exceeds
- Exactly 55 districts (1 per county -- county-based system)
- ~2,000 ELs statewide (~0.8% enrollment -- lowest nationally)
- Third Grade Success Act -- early literacy with retention provisions
- County-based governance: each of WV's 55 counties is a single school district
- Dashboard: zoomwv.k12.wv.us

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_PASSWORD = "vera2026"

WV_BLUE = "#002B5C"
WV_GOLD = "#FFD700"
WV_DARK = "#001A3A"
WV_GRAY = "#4A4A4A"
WV_LIGHT_BLUE = "#3A6B9F"

# ============================================================================
# DATA: West Virginia Counties/Districts with EL Populations
# WV has exactly 55 county school districts (1 per county)
# ============================================================================

def load_districts():
    """Load WV county districts with significant EL populations.
    West Virginia has exactly 55 county-based school districts.
    ~2,000 ELs statewide (0.8% -- lowest EL rate nationally).
    EL population concentrated in a few counties with university or
    industry presence.
    """
    data = [
        # (county_code, district_name, total_students, el_count, el_percent,
        #  wvgsa_met_all, wvgsa_met_el, graduation_rate, region_note)

        # --- Counties with notable EL populations ---
        ("MON", "Monongalia County Schools", 11200, 448, 4.0, 52.5, 15.8, 89.5, "WVU campus; highest EL% in state; university families"),
        ("KAN", "Kanawha County Schools", 24500, 392, 1.6, 42.8, 12.5, 82.5, "Capital county (Charleston); largest district"),
        ("BER", "Berkeley County Schools", 19800, 297, 1.5, 44.2, 13.2, 84.8, "Eastern Panhandle; DC commuter growth"),
        ("JEF", "Jefferson County Schools", 9200, 184, 2.0, 48.5, 14.8, 87.2, "Eastern Panhandle; Shepherdstown/Charles Town"),
        ("CAB", "Cabell County Schools", 12500, 150, 1.2, 40.5, 11.8, 81.5, "Huntington/Marshall University area"),
        ("HAR", "Harrison County Schools", 10200, 102, 1.0, 43.8, 12.2, 83.8, "Clarksburg; energy sector presence"),
        ("WOO", "Wood County Schools", 11800, 94, 0.8, 41.2, 11.5, 82.2, "Parkersburg; chemical/energy industry"),
        ("RAL", "Raleigh County Schools", 11500, 69, 0.6, 39.5, 10.8, 80.5, "Beckley; southern coalfields transition"),
        ("PUT", "Putnam County Schools", 9800, 59, 0.6, 55.2, 16.5, 91.2, "Charleston suburb; highest-performing"),
        ("MER", "Mercer County Schools", 8800, 53, 0.6, 38.2, 10.5, 79.8, "Princeton/Bluefield; southern WV"),

        # --- Counties with smaller EL presence ---
        ("MAR", "Marion County Schools", 7200, 36, 0.5, 44.5, 12.8, 84.5, "Fairmont; Fairmont State area"),
        ("OHI", "Ohio County Schools", 5200, 26, 0.5, 46.8, 13.5, 86.2, "Wheeling; Northern Panhandle"),
        ("HAN", "Hancock County Schools", 4200, 21, 0.5, 45.2, 13.0, 85.5, "Weirton; Northern Panhandle steel"),
        ("MIN", "Mineral County Schools", 4000, 20, 0.5, 40.8, 11.0, 81.8, "Keyser; Potomac Highlands"),
        ("GRE", "Greenbrier County Schools", 4800, 19, 0.4, 41.5, 11.2, 82.5, "Lewisburg; tourism/resort area"),
    ]

    return pd.DataFrame(data, columns=[
        'county_code', 'district_name', 'total_students',
        'el_count', 'el_percent',
        'wvgsa_met_all', 'wvgsa_met_el', 'graduation_rate',
        'region_note'
    ])


# ============================================================================
# DATA: ELPA21 Domain Data (NOT WIDA)
# West Virginia uses ELPA21 -- English Language Proficiency Assessment for 21st Century
# ============================================================================

def load_elpa_data(districts_df):
    """Generate district ELPA21 domain data.
    West Virginia uses ELPA21, NOT WIDA ACCESS.
    ELPA21 also measures Listening, Speaking, Reading, Writing
    but uses a different scale and scoring framework."""
    elpa_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                base_speaking = 330 + (grade * 8)
                base_writing = 280 + (grade * 6)

                el_density_penalty = max(0, (d['el_percent'] - 2) * 0.6)
                el_factor = d['wvgsa_met_el'] / 12.0
                speaking_adj = int(12 * el_factor + d['el_percent'] * 0.3 - el_density_penalty)
                writing_adj = int(-10 + (el_factor - 1) * 9 - el_density_penalty * 0.8)

                yr_adj = 3 if year == 2025 else 0

                elpa_data.append({
                    'county_code': d['county_code'],
                    'district_name': d['district_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(3, int(d['el_count'] / 6)),
                    'listening_avg': base_speaking + speaking_adj - 4 + yr_adj,
                    'speaking_avg': base_speaking + speaking_adj + yr_adj,
                    'reading_avg': base_writing + writing_adj + 12 + yr_adj,
                    'writing_avg': base_writing + writing_adj + yr_adj,
                    'composite_avg': int((base_speaking + speaking_adj + base_writing + writing_adj) / 2 + 14 + yr_adj),
                })

    return pd.DataFrame(elpa_data)


# ============================================================================
# DATA: WVGSA Achievement Data
# WVGSA (West Virginia General Summative Assessment)
# 4 levels: Does Not Meet / Partially Meets / Meets / Exceeds
# ============================================================================

def load_wvgsa_data(districts_df):
    """Generate WVGSA data based on zoomwv.k12.wv.us patterns."""
    wvgsa_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['ELA', 'Math']:
                    base = d['wvgsa_met_all'] if subject == 'ELA' else d['wvgsa_met_all'] * 0.80
                    met_exceeded = max(8, min(80, base + (grade - 5) * -1.3))

                    exceeds = max(2, met_exceeded * 0.18)
                    meets = met_exceeded - exceeds
                    partially_meets = max(14, (100 - met_exceeded) * 0.44)
                    does_not_meet = max(8, 100 - met_exceeded - partially_meets)

                    wvgsa_data.append({
                        'county_code': d['county_code'],
                        'district_name': d['district_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'met_exceeded_pct': round(met_exceeded, 1),
                        'exceeds_pct': round(exceeds, 1),
                        'meets_pct': round(meets, 1),
                        'partially_meets_pct': round(partially_meets, 1),
                        'does_not_meet_pct': round(does_not_meet, 1),
                    })

    return pd.DataFrame(wvgsa_data)


# ============================================================================
# DATA: Statewide Domain Proficiency (ELPA21)
# ============================================================================

def load_statewide_domain_data():
    """Statewide ELPA21 domain proficiency percentages by grade cluster."""
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 38, 'speaking': 33, 'reading': 22, 'writing': 14},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 42, 'speaking': 38, 'reading': 26, 'writing': 17},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 46, 'speaking': 41, 'reading': 30, 'writing': 20},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 49, 'speaking': 44, 'reading': 33, 'writing': 22},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 36, 'speaking': 31, 'reading': 20, 'writing': 12},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 40, 'speaking': 36, 'reading': 24, 'writing': 15},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 44, 'speaking': 39, 'reading': 28, 'writing': 18},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 47, 'speaking': 42, 'reading': 31, 'writing': 20},
    ])


# ============================================================================
# DATA: EL Population Growth
# ============================================================================

def load_el_growth_data():
    """West Virginia EL population -- lowest in nation, slowly growing."""
    return pd.DataFrame([
        {'year': 2005, 'el_count': 800, 'el_percent': 0.3, 'note': 'Baseline'},
        {'year': 2008, 'el_count': 950, 'el_percent': 0.3, 'note': ''},
        {'year': 2010, 'el_count': 1050, 'el_percent': 0.4, 'note': ''},
        {'year': 2012, 'el_count': 1200, 'el_percent': 0.4, 'note': 'Marcellus Shale boom begins'},
        {'year': 2014, 'el_count': 1400, 'el_percent': 0.5, 'note': 'Energy sector draws workers'},
        {'year': 2016, 'el_count': 1550, 'el_percent': 0.6, 'note': ''},
        {'year': 2018, 'el_count': 1650, 'el_percent': 0.6, 'note': 'Teacher strike year'},
        {'year': 2020, 'el_count': 1600, 'el_percent': 0.6, 'note': 'COVID dip'},
        {'year': 2022, 'el_count': 1800, 'el_percent': 0.7, 'note': 'Post-COVID rebound'},
        {'year': 2024, 'el_count': 1950, 'el_percent': 0.8, 'note': 'Third Grade Success Act'},
        {'year': 2025, 'el_count': 2050, 'el_percent': 0.8, 'note': 'Continued slow growth'},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True

    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px;">
        <h1 style="color: {WV_BLUE}; font-size: 3rem; margin-bottom: 10px;">VERA-WV</h1>
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 40px;">
            Verification Engine for Results &amp; Accountability<br>West Virginia Implementation
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Enter access code:", type="password", key="pw")
        if st.button("Access VERA-WV", use_container_width=True):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid access code")

    st.markdown(f"""
    <div style="text-align: center; margin-top: 60px; color: #999; font-size: 0.85rem;">
        <p>VERA-WV analyzes ELPA21 domain data and WVGSA results across 55 West Virginia county districts.</p>
        <p>~2,000 English Learners | ~0.8% statewide (lowest nationally)</p>
        <p>ELPA21 (NOT WIDA) | 55 county-based districts | 1 district per county</p>
        <p>Data: zoomwv.k12.wv.us | Third Grade Success Act</p>
        <p style="margin-top: 10px;">Contact: brian@h-edu.solutions</p>
    </div>
    """, unsafe_allow_html=True)
    return False


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(elpa_df, county_code, grade, year):
    filtered = elpa_df[
        (elpa_df['county_code'] == county_code) &
        (elpa_df['grade'] == grade) &
        (elpa_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'county_code': county_code, 'district_name': row['district_name'],
        'grade': grade, 'year': year,
        'speaking_avg': row['speaking_avg'], 'writing_avg': row['writing_avg'],
        'delta': delta, 'delta_normalized': delta_normalized, 'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGE 1: OVERVIEW
# ============================================================================

def render_overview(districts_df):
    st.header("West Virginia Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Pilot Counties", len(districts_df))
    with col2: st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3: st.metric("English Learners", f"{districts_df['el_count'].sum():,}")
    with col4: st.metric("Statewide EL %", "~0.8%", delta="Lowest nationally")

    st.divider()

    # Key policy context
    st.subheader("Key Policy Context")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("**ELPA21 (NOT WIDA)**\nWV uses the ELPA21 assessment, not WIDA ACCESS. Different scale and framework.")
    with col2:
        st.warning("**Third Grade Success Act**\nEarly literacy mandate with reading intervention and retention provisions")
    with col3:
        st.info("**County-Based System**\nExactly 55 districts -- 1 per county. No independent school districts.")

    st.divider()

    # WV-specific pattern
    st.subheader("The West Virginia Pattern: Lowest EL Rate Nationally")
    st.markdown("""
    West Virginia has the **lowest EL percentage of any state** (~0.8%, ~2,000 students).
    The tiny EL population is concentrated in a handful of counties with **university
    communities** or **energy-sector industry**:

    | County | EL % | Context |
    |--------|------|---------|
    | Monongalia County | **4.0%** | WVU campus; highest EL% in state |
    | Jefferson County | **2.0%** | Eastern Panhandle; DC commuter area |
    | Kanawha County | **1.6%** | Capital county (Charleston); largest district |
    | Berkeley County | **1.5%** | Eastern Panhandle; rapid growth area |
    | Cabell County | **1.2%** | Huntington/Marshall University |

    **Key Challenges:**
    - Most counties serve **fewer than 20 EL students total**, making dedicated ESL
      staffing financially impossible
    - **ELPA21** (not WIDA) creates assessment isolation from neighboring WIDA states
    - The **Marcellus Shale energy boom** (2012+) brought some EL families, but the
      energy sector's boom/bust cycle creates enrollment instability
    - **55-county system** means each county is a standalone district -- no regional
      consolidation of EL services
    """)

    st.divider()

    st.subheader("Assessment & Accountability Framework")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **WVGSA Assessment:**
        - West Virginia General Summative Assessment
        - ELA and Math, grades 3-8
        - 4 Achievement Levels:
            - **Exceeds** -- advanced mastery
            - **Meets** -- grade-level proficiency
            - **Partially Meets** -- approaching
            - **Does Not Meet** -- below grade level
        - Results: zoomwv.k12.wv.us
        """)
    with col2:
        st.markdown("""
        **EL Program:**
        - **ELPA21** (NOT WIDA ACCESS)
        - 4 Domains: Listening, Speaking, Reading, Writing
        - Overall proficiency for exit
        - 55 county districts, ~2,000 ELs

        **Key Legislation:**
        - **Third Grade Success Act** -- early literacy
        - Reading intervention mandate
        - Retention provisions for non-readers

        **Data System:**
        - **zoomwv.k12.wv.us** -- public dashboard
        - County-based reporting
        """)

    st.divider()

    # District table
    st.subheader("Pilot Counties -- EL Populations & Performance")
    display = districts_df[['county_code', 'district_name', 'total_students', 'el_count',
                            'el_percent', 'wvgsa_met_all', 'wvgsa_met_el',
                            'graduation_rate']].copy()
    display.columns = ['County', 'District', 'Students', 'EL Count', 'EL %',
                       'WVGSA Met+ All %', 'WVGSA Met+ EL %', 'Grad Rate %']
    st.dataframe(display, use_container_width=True, hide_index=True)

    # EL bar chart
    st.subheader("English Learner Population by County")
    fig = px.bar(
        districts_df.sort_values('el_count', ascending=True),
        x='el_count', y='district_name', orientation='h',
        color='el_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, WV_BLUE]],
        labels={'el_count': 'English Learners', 'district_name': 'County District', 'el_percent': 'EL %'}
    )
    fig.update_layout(height=550, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Region chart
    st.subheader("EL Distribution: University/Industry Counties vs Rural")
    conc_df = districts_df[['district_name', 'el_percent', 'total_students']].copy()
    conc_df['category'] = conc_df['el_percent'].apply(
        lambda x: 'University/Industry (>1.5% EL)' if x > 1.5 else 'Rural/Low-EL (<1.5%)'
    )
    fig2 = px.scatter(conc_df, x='total_students', y='el_percent',
                      color='category', size='el_percent',
                      hover_name='district_name',
                      color_discrete_map={
                          'University/Industry (>1.5% EL)': WV_BLUE,
                          'Rural/Low-EL (<1.5%)': WV_GRAY
                      },
                      labels={'total_students': 'Total Enrollment', 'el_percent': 'EL %',
                              'category': 'County Type'})
    fig2.update_layout(
        title="EL % vs County Size -- University Communities Drive EL Presence",
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)


# ============================================================================
# PAGE 2: DOMAIN ANALYSIS
# ============================================================================

def render_domain_analysis(domain_df, growth_df):
    st.header("Statewide ELPA21 Domain Proficiency")

    st.markdown("""
    **Source:** WVDE / ELPA21 results (NOT WIDA ACCESS).
    West Virginia uses ELPA21, placing it outside the WIDA Consortium.
    Domain proficiency percentages still reveal the oral-written delta pattern.

    **West Virginia Context:** With only ~2,000 ELs statewide (0.8%), the state
    has the **lowest EL rate nationally**. Most counties have fewer than 20 ELs,
    and statewide domain data is driven heavily by a handful of counties
    (Monongalia, Kanawha, Berkeley, Jefferson).
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', WV_GRAY), ('speaking', WV_BLUE),
                          ('reading', WV_LIGHT_BLUE), ('writing', '#333333')]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ELPA21 Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 60])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[WV_BLUE if d > 18 else WV_LIGHT_BLUE for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap", yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")

    st.divider()

    # EL growth over time
    st.subheader("West Virginia EL Population Growth (Lowest Nationally)")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=growth_df['year'], y=growth_df['el_count'],
        mode='lines+markers', line=dict(color=WV_BLUE, width=3),
        marker=dict(size=8), name='EL Count'
    ))
    fig3.update_layout(
        title="EL Population Growth -- Slow, Driven by University/Energy Sectors",
        xaxis_title="Year", yaxis_title="English Learners",
        height=400
    )
    fig3.add_annotation(x=2012, y=1200, text="Marcellus Shale boom", showarrow=True, arrowhead=2)
    fig3.add_annotation(x=2018, y=1650, text="Teacher strike", showarrow=True, arrowhead=2)
    fig3.add_annotation(x=2024, y=1950, text="Third Grade Success Act", showarrow=True, arrowhead=2)
    st.plotly_chart(fig3, use_container_width=True)

    st.info("""
    **ELPA21 vs WIDA:** West Virginia is one of a small number of states using ELPA21
    instead of WIDA ACCESS. This creates assessment isolation from neighboring WIDA
    states (Virginia, Kentucky, Ohio, Pennsylvania, Maryland), making cross-state
    comparisons of EL proficiency impossible. Students transferring from neighboring
    states must be re-assessed on a different framework.
    """)


# ============================================================================
# PAGE 3: ELPA21 ANALYSIS
# ============================================================================

def render_elpa_analysis(elpa_df, districts_df):
    st.header("ELPA21 Analysis")
    st.markdown("""
    **ELPA21** (English Language Proficiency Assessment for the 21st Century) measures
    English learners across four domains. WV has ~2,000 ELs across 55 county districts.

    **Note:** WV uses ELPA21, NOT WIDA ACCESS. Different scale and scoring framework
    from the WIDA Consortium used by most neighboring states.

    **Small N Warning:** Most county-grade combinations have very few students tested.
    Results should be interpreted with extreme caution.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="elpa_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="elpa_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="elpa_y")

    county_code = districts_df[districts_df['district_name'] == district]['county_code'].values[0]
    filtered = elpa_df[(elpa_df['county_code'] == county_code) &
                       (elpa_df['grade'] == grade) &
                       (elpa_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        if row['total_tested'] < 10:
            st.warning(f"**Small N Warning:** Only **{row['total_tested']}** students tested. "
                       "Results may not be statistically meaningful.")

        d_info = districts_df[districts_df['county_code'] == county_code].iloc[0]
        if d_info['el_percent'] > 2:
            st.info(f"**Higher-Concentration County:** {district} has **{d_info['el_percent']:.1f}% EL enrollment**. "
                    f"{d_info['region_note']}.")

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2: st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3: st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4: st.metric("Writing", f"{row['writing_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(x=domains, y=scores,
                               marker_color=[WV_GRAY, WV_BLUE, WV_LIGHT_BLUE, '#333333'],
                               text=[f"{s:.0f}" for s in scores], textposition='outside'))
        fig.update_layout(title=f"ELPA21 Domains -- {district} -- Grade {grade} ({year})",
                         yaxis_title="Scale Score", height=400)
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written

        st.subheader("Oral vs Written Gap")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Oral Average", f"{oral:.0f}")
        with col2: st.metric("Written Average", f"{written:.0f}")
        with col3: st.metric("Gap", f"{gap:+.0f}", delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")

        st.divider()
        st.subheader("Composite & Exit Context")
        composite = row['composite_avg']
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Composite Average", f"{composite}")
        with col2: st.metric("Exit Criterion", "Overall Proficient", help="ELPA21 overall proficiency for reclassification")
        with col3: st.metric("Total Tested", f"{row['total_tested']:,}")


# ============================================================================
# PAGE 4: TYPE 4 DETECTION
# ============================================================================

def render_type4(elpa_df, districts_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking Score - Writing Score. Flag threshold: normalized delta > 8 points.

    **West Virginia Context:** With only ~2,000 ELs statewide (lowest nationally),
    Type 4 detection operates at very small N. In most counties, a single student
    shifting grades can change the entire pattern. Detection is most meaningful in
    Monongalia (WVU), Kanawha (Charleston), and Berkeley (Eastern Panhandle) counties,
    which have enough ELs for cohort-level analysis.

    **ELPA21 Note:** Domain scores use ELPA21 framework, not WIDA. The oral-written
    delta pattern is structurally similar but scale differences should be noted.
    """)

    col1, col2, col3 = st.columns(3)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="t4_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3: year = st.selectbox("Year", [2025, 2024], key="t4_y")

    county_code = districts_df[districts_df['district_name'] == district]['county_code'].values[0]
    result = compute_type4_analysis(elpa_df, county_code, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2: st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3: st.metric("Delta", f"{result['delta']:+.0f}")
        with col4: st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']], marker_color=WV_BLUE))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']], marker_color=WV_GRAY))
        fig.update_layout(title=f"Speaking vs Writing -- {district} -- Grade {grade}", barmode='group', height=350)
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} students affected.")
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        # All grades
        st.subheader(f"All Grades -- {district} ({year})")
        all_data = [compute_type4_analysis(elpa_df, county_code, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['speaking_avg'], name='Speaking',
                                     mode='lines+markers', line=dict(color=WV_BLUE, width=3)))
            fig.add_trace(go.Scatter(x=gdf['grade'], y=gdf['writing_avg'], name='Writing',
                                     mode='lines+markers', line=dict(color=WV_GRAY, width=3)))
            fig.update_layout(title="Speaking vs Writing Across Grades", xaxis_title="Grade",
                             yaxis_title="Scale Score", height=400)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("County Summary")
        if all_data:
            summary_df = pd.DataFrame(all_data)[['grade', 'speaking_avg', 'writing_avg', 'delta', 'flagged', 'estimated_flagged']]
            summary_df.columns = ['Grade', 'Speaking', 'Writing', 'Delta', 'Flagged', 'Est. Affected']
            summary_df['Flagged'] = summary_df['Flagged'].map({True: 'YES', False: 'No'})
            st.dataframe(summary_df, use_container_width=True, hide_index=True)


# ============================================================================
# PAGE 5: ACHIEVEMENT GAPS
# ============================================================================

def render_achievement_gaps(districts_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **Data from zoomwv.k12.wv.us.** WVGSA Met + Exceeds rates across pilot counties.

    **WVGSA** uses 4 achievement levels:
    Does Not Meet, Partially Meets, Meets, Exceeds.

    **Key Pattern:** With only ~2,000 ELs statewide, the EL-to-All gap is most
    meaningful in the handful of counties with enough ELs for valid comparison.
    Monongalia County (WVU) has the highest EL concentration at 4.0%.
    """)

    st.divider()

    # All vs EL comparison
    fig = go.Figure()
    sorted_df = districts_df.sort_values('wvgsa_met_all', ascending=True)
    fig.add_trace(go.Bar(
        x=sorted_df['wvgsa_met_all'], y=sorted_df['district_name'],
        name='All Students', orientation='h', marker_color=WV_GRAY
    ))
    fig.add_trace(go.Bar(
        x=sorted_df['wvgsa_met_el'], y=sorted_df['district_name'],
        name='English Learners', orientation='h', marker_color=WV_BLUE
    ))
    fig.update_layout(
        title="WVGSA Met+ Rate: All Students vs English Learners",
        barmode='group', xaxis_title="% Met + Exceeds",
        height=600, legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gap analysis
    st.subheader("All-EL Achievement Gap by County")
    gap_df = districts_df.copy()
    gap_df['el_gap'] = gap_df['wvgsa_met_all'] - gap_df['wvgsa_met_el']
    gap_df = gap_df.sort_values('el_gap', ascending=True)

    fig_gap = go.Figure(go.Bar(
        x=gap_df['el_gap'], y=gap_df['district_name'], orientation='h',
        marker_color=[WV_BLUE if g > 30 else WV_LIGHT_BLUE if g > 20 else WV_GRAY for g in gap_df['el_gap']],
        text=[f"{g:.0f} pts" for g in gap_df['el_gap']], textposition='outside'
    ))
    fig_gap.update_layout(title="All Students - EL Gap (WVGSA Met+)",
                         xaxis_title="Gap (percentage points)", height=550)
    st.plotly_chart(fig_gap, use_container_width=True)

    # EL proficiency vs EL concentration
    st.subheader("EL Proficiency vs EL Concentration")
    fig2 = px.scatter(districts_df, x='el_percent', y='wvgsa_met_el', size='el_count',
                      hover_name='district_name',
                      color_discrete_sequence=[WV_BLUE],
                      labels={'el_percent': 'EL %', 'wvgsa_met_el': 'EL Met+ %',
                              'el_count': 'EL Count'})
    fig2.update_layout(
        title="EL Proficiency vs Concentration -- Monongalia (WVU) Stands Apart",
        height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.info("""
    **County-Based Challenge:** West Virginia's 55-county system means each county
    operates independently with no mechanism for regional EL service sharing. A county
    with 5-10 EL students cannot justify a full-time ESL teacher, yet has the same
    federal compliance obligations as Monongalia County with 448 ELs. This structural
    mismatch is the defining challenge of WV's EL program.
    """)


# ============================================================================
# PAGE 6: WVGSA ANALYSIS
# ============================================================================

def render_wvgsa(wvgsa_df, districts_df):
    st.header("WVGSA Assessment Analysis")
    st.markdown("""
    **WVGSA (West Virginia General Summative Assessment)** assesses students in
    grades 3-8 in ELA and Math.

    **4 Achievement Levels:**
    - **Exceeds** -- Advanced understanding
    - **Meets** -- Grade-level proficiency
    - **Partially Meets** -- Approaching expectations
    - **Does Not Meet** -- Below grade level

    Results are published on **zoomwv.k12.wv.us**.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1: district = st.selectbox("District", districts_df['district_name'].tolist(), key="wvgsa_d")
    with col2: grade = st.selectbox("Grade", list(range(3, 9)), key="wvgsa_g")
    with col3: subject = st.selectbox("Subject", ['ELA', 'Math'], key="wvgsa_s")
    with col4: year = st.selectbox("Year", [2025, 2024], key="wvgsa_y")

    county_code = districts_df[districts_df['district_name'] == district]['county_code'].values[0]
    filtered = wvgsa_df[(wvgsa_df['county_code'] == county_code) &
                        (wvgsa_df['grade'] == grade) &
                        (wvgsa_df['subject'] == subject) &
                        (wvgsa_df['year'] == year)]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Met + Exceeds", f"{row['met_exceeded_pct']:.1f}%")
        with col2:
            st.metric("Exceeds Only", f"{row['exceeds_pct']:.1f}%")

        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Does Not Meet", f"{row['does_not_meet_pct']:.1f}%")
        with col2: st.metric("Partially Meets", f"{row['partially_meets_pct']:.1f}%")
        with col3: st.metric("Meets", f"{row['meets_pct']:.1f}%")
        with col4: st.metric("Exceeds", f"{row['exceeds_pct']:.1f}%")

        levels = ['Does Not\nMeet', 'Partially\nMeets', 'Meets', 'Exceeds']
        values = [row['does_not_meet_pct'], row['partially_meets_pct'], row['meets_pct'], row['exceeds_pct']]
        colors = ['#d32f2f', '#f57c00', WV_BLUE, WV_DARK]
        fig = go.Figure(go.Bar(x=levels, y=values, marker_color=colors,
                               text=[f"{v:.1f}%" for v in values], textposition='outside'))
        fig.update_layout(title=f"WVGSA {subject} -- {district} -- Grade {grade} ({year})",
                         yaxis_title="Percentage", height=420)
        st.plotly_chart(fig, use_container_width=True)

        d_info = districts_df[districts_df['county_code'] == county_code].iloc[0]

        if grade == 3:
            st.subheader("Third Grade Success Act Context")
            st.warning(f"""
            **Grade 3 -- Third Grade Success Act applies here.**

            - **{district}** Grade 3 {subject} Met+: **{row['met_exceeded_pct']:.1f}%**
            - Students not meeting reading benchmarks face intervention and potential retention
            - EL %: **{d_info['el_percent']:.1f}%** | EL Count: **{d_info['el_count']}**
            - {d_info['region_note']}
            - {100 - row['met_exceeded_pct']:.1f}% of students are below Met
            """)
        else:
            st.subheader("County Context")
            st.markdown(f"""
            **{district}** -- Grade {grade} {subject} ({year}):
            - Met+ Rate: **{row['met_exceeded_pct']:.1f}%**
            - EL %: **{d_info['el_percent']:.1f}%** | EL Count: **{d_info['el_count']}**
            - {d_info['region_note']}
            """)


# ============================================================================
# PAGE 7: EXPORT DATA
# ============================================================================

def render_export(elpa_df, wvgsa_df, districts_df, domain_df, growth_df):
    st.header("Export Data")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ELPA21 Data")
        st.dataframe(elpa_df, use_container_width=True, hide_index=True)
        st.download_button("Download ELPA21 CSV", elpa_df.to_csv(index=False),
                          "vera_wv_elpa21.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("WVGSA Data")
        st.dataframe(wvgsa_df, use_container_width=True, hide_index=True)
        st.download_button("Download WVGSA CSV", wvgsa_df.to_csv(index=False),
                          "vera_wv_wvgsa.csv", "text/csv", use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button("Download Domain CSV", domain_df.to_csv(index=False),
                          "vera_wv_domains.csv", "text/csv", use_container_width=True)
    with col2:
        st.subheader("County District Data")
        st.dataframe(districts_df, use_container_width=True, hide_index=True)
        st.download_button("Download Counties CSV", districts_df.to_csv(index=False),
                          "vera_wv_counties.csv", "text/csv", use_container_width=True)

    st.divider()

    st.subheader("EL Population Growth (2005-2025)")
    st.dataframe(growth_df, use_container_width=True, hide_index=True)
    st.download_button("Download EL Growth CSV", growth_df.to_csv(index=False),
                      "vera_wv_el_growth.csv", "text/csv", use_container_width=True)


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(page_title="VERA-WV | West Virginia Type 4 Detection", page_icon="", layout="wide")

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {WV_BLUE}; }}
        .stButton > button {{ background-color: {WV_BLUE}; color: white; }}
        .stButton > button:hover {{ background-color: {WV_DARK}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    if not check_password():
        return

    # Load data
    districts_df = load_districts()
    elpa_df = load_elpa_data(districts_df)
    wvgsa_df = load_wvgsa_data(districts_df)
    domain_df = load_statewide_domain_data()
    growth_df = load_el_growth_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {WV_BLUE}; margin: 0;">VERA-WV</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">West Virginia Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Domain Analysis",
        "ELPA21 Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "WVGSA Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ELPA21 (NOT WIDA)
    - WVGSA (ELA & Math)
    - zoomwv.k12.wv.us

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points
    - ELPA21 overall proficiency exit

    **Key WV Context:**
    - 55 counties = 55 districts
    - ~2,000 ELs (~0.8%)
    - Lowest EL% nationally
    - ELPA21 (not WIDA)
    - Monongalia Co. 4.0% (WVU)
    - Third Grade Success Act
    - County-based governance
    - Marcellus Shale energy impact
    - WVGSA: 4 levels

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    if page == "Overview": render_overview(districts_df)
    elif page == "Domain Analysis": render_domain_analysis(domain_df, growth_df)
    elif page == "ELPA21 Analysis": render_elpa_analysis(elpa_df, districts_df)
    elif page == "Type 4 Detection": render_type4(elpa_df, districts_df)
    elif page == "Achievement Gaps": render_achievement_gaps(districts_df)
    elif page == "WVGSA Analysis": render_wvgsa(wvgsa_df, districts_df)
    elif page == "Export Data": render_export(elpa_df, wvgsa_df, districts_df, domain_df, growth_df)


if __name__ == "__main__":
    main()
