# app_matplotlib.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Palo Alto Networks - Engagement & Burnout", page_icon="🏢", layout="wide")

# Custom CSS for KPIs and background
st.markdown("""
<style>
    /* New background color for the entire app */
    .stApp {
        background-color: #f5f5f5;
    }
    .main-header { font-size: 2.5rem; color: #0066B3; text-align: center; margin-bottom: 1rem; }
    .kpi-card { background-color: #f0f2f6; padding: 1rem; border-radius: 10px; text-align: center; border-left: 4px solid #0066B3; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #0066B3; }
    .metric-label { font-size: 0.9rem; color: #555; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">🏢 Palo Alto Networks</p>', unsafe_allow_html=True)
st.markdown('<h2 style="text-align: center; color: #333;">Employee Engagement, Satisfaction & Burnout Diagnostic Dashboard</h2>', unsafe_allow_html=True)
st.markdown("---")

# Load and process data
@st.cache_data
def load_data():
    df = pd.read_csv('Palo Alto Networks.csv')
    df['Engagement_Index'] = (df['JobInvolvement'] + df['JobSatisfaction'] + 
                              df['EnvironmentSatisfaction'] + df['RelationshipSatisfaction']) / 4
    df['Engagement_Level'] = pd.cut(df['Engagement_Index'], bins=[0, 1.5, 2.5, 3.5, 4.0],
                                    labels=['Severely Disengaged', 'Disengaged', 'Moderately Engaged', 'Highly Engaged'])
    df['Burnout_Risk'] = 'Low Risk'
    df.loc[(df['OverTime'] == 'Yes') & (df['WorkLifeBalance'] <= 2), 'Burnout_Risk'] = 'High Risk'
    df.loc[((df['OverTime'] == 'Yes') | (df['WorkLifeBalance'] <= 2)) & (df['Burnout_Risk'] == 'Low Risk'), 'Burnout_Risk'] = 'Medium Risk'
    return df

df = load_data()

# Sidebar filters
st.sidebar.markdown("## 🔍 Filter Controls")
selected_dept = st.sidebar.selectbox("Select Department", ['All'] + sorted(df['Department'].unique().tolist()))
selected_role = st.sidebar.selectbox("Select Job Role", ['All'] + sorted(df['JobRole'].unique().tolist()))
overtime_filter = st.sidebar.selectbox("Overtime Status", ['All', 'Yes', 'No'])
engagement_threshold = st.sidebar.slider("Engagement Index Threshold", 1.0, 4.0, 2.5, 0.1)
tenure_min, tenure_max = int(df['YearsAtCompany'].min()), int(df['YearsAtCompany'].max())
tenure_range = st.sidebar.slider("Years at Company", tenure_min, tenure_max, (tenure_min, tenure_max))

filtered_df = df.copy()
if selected_dept != 'All': filtered_df = filtered_df[filtered_df['Department'] == selected_dept]
if selected_role != 'All': filtered_df = filtered_df[filtered_df['JobRole'] == selected_role]
if overtime_filter != 'All': filtered_df = filtered_df[filtered_df['OverTime'] == overtime_filter]
filtered_df = filtered_df[(filtered_df['YearsAtCompany'] >= tenure_range[0]) & (filtered_df['YearsAtCompany'] <= tenure_range[1])]

# ============ KPIs ============
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.markdown(f"""<div class="kpi-card"><div class="metric-value">{filtered_df['Engagement_Index'].mean():.2f}</div><div class="metric-label">📈 Engagement Index</div><div style="font-size:0.8rem;">out of 4.0</div></div>""", unsafe_allow_html=True)
with col2:
    burnout_high = (filtered_df['Burnout_Risk'] == 'High Risk').sum()
    st.markdown(f"""<div class="kpi-card"><div class="metric-value" style="color:#FF4444;">{(burnout_high/len(filtered_df))*100:.1f}%</div><div class="metric-label">⚠️ High Burnout Risk</div><div style="font-size:0.8rem;">{burnout_high} employees</div></div>""", unsafe_allow_html=True)
with col3: st.markdown(f"""<div class="kpi-card"><div class="metric-value">{filtered_df['WorkLifeBalance'].mean():.2f}</div><div class="metric-label">⚖️ Work-Life Balance</div><div style="font-size:0.8rem;">out of 4.0</div></div>""", unsafe_allow_html=True)
with col4:
    overtime_pct = (filtered_df['OverTime'] == 'Yes').mean() * 100
    st.markdown(f"""<div class="kpi-card"><div class="metric-value">{overtime_pct:.1f}%</div><div class="metric-label">🕐 Overtime Rate</div><div style="font-size:0.8rem;">{filtered_df['OverTime'].value_counts().get('Yes', 0)} employees</div></div>""", unsafe_allow_html=True)
with col5:
    attrition_pct = (filtered_df['Attrition'] == 1).mean() * 100
    color = '#FF4444' if attrition_pct > 12 else '#00AA00'
    st.markdown(f"""<div class="kpi-card"><div class="metric-value" style="color:{color};">{attrition_pct:.1f}%</div><div class="metric-label">🚪 Attrition Rate</div><div style="font-size:0.8rem;">{filtered_df['Attrition'].sum()} employees</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# ============ Engagement Overview ============
st.markdown("## 📈 Engagement Health Overview")
col1, col2 = st.columns([2, 1])

with col1:
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = {'Low Risk': '#00AA00', 'Medium Risk': '#FFA500', 'High Risk': '#FF4444'}
    for risk, color in colors.items():
        subset = filtered_df[filtered_df['Burnout_Risk'] == risk]
        ax.hist(subset['Engagement_Index'], bins=30, alpha=0.6, label=risk, color=color, density=False)
    ax.axvline(x=engagement_threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold: {engagement_threshold}')
    ax.set_xlabel('Engagement Index')
    ax.set_ylabel('Number of Employees')
    ax.set_title('Engagement Distribution by Burnout Risk')
    ax.legend()
    st.pyplot(fig)
    plt.close(fig)

with col2:
    engagement_counts = filtered_df['Engagement_Level'].value_counts()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(engagement_counts.values, labels=engagement_counts.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Blues(np.linspace(0.4, 0.9, len(engagement_counts))))
    ax.set_title('Engagement Levels')
    st.pyplot(fig)
    plt.close(fig)

st.markdown("### Satisfaction Dimension Breakdown")
fig, ax = plt.subplots(figsize=(10, 5))
satisfaction_dims = ['JobSatisfaction','EnvironmentSatisfaction','RelationshipSatisfaction','WorkLifeBalance','JobInvolvement']
data_to_plot = [filtered_df[dim].dropna() for dim in satisfaction_dims]
ax.boxplot(data_to_plot, tick_labels=satisfaction_dims, patch_artist=True)
ax.set_ylabel('Score (1-4)')
ax.set_title('Satisfaction Dimensions Distribution')
ax.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig)
plt.close(fig)
st.markdown("---")

# ============ Burnout Risk Dashboard ============
st.markdown("## 🔥 Burnout Risk Dashboard")
col1, col2 = st.columns(2)

with col1:
    burnout_counts = filtered_df['Burnout_Risk'].value_counts()
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = {'Low Risk': '#00AA00', 'Medium Risk': '#FFA500', 'High Risk': '#FF4444'}
    ax.bar(burnout_counts.index, burnout_counts.values, color=[colors[x] for x in burnout_counts.index])
    ax.set_xlabel('Risk Level')
    ax.set_ylabel('Number of Employees')
    ax.set_title('Burnout Risk Distribution')
    for i, v in enumerate(burnout_counts.values):
        ax.text(i, v + 5, str(v), ha='center', va='bottom')
    st.pyplot(fig)
    plt.close(fig)

with col2:
    overtime_wlb = filtered_df.groupby(['OverTime', 'Burnout_Risk']).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(6, 4))
    overtime_wlb.plot(kind='bar', ax=ax, color=['#00AA00','#FFA500','#FF4444'])
    ax.set_xlabel('Overtime Status')
    ax.set_ylabel('Count')
    ax.set_title('Overtime vs Burnout Risk')
    ax.legend(title='Burnout Risk')
    st.pyplot(fig)
    plt.close(fig)

st.markdown("### Risk Factor Correlation Matrix")
fig, ax = plt.subplots(figsize=(8, 6))
risk_factors = ['Engagement_Index','WorkLifeBalance','JobSatisfaction','EnvironmentSatisfaction','RelationshipSatisfaction','JobInvolvement']
corr = filtered_df[risk_factors].corr()
sns.heatmap(corr, annot=True, cmap='RdBu_r', center=0, vmin=-1, vmax=1, fmt='.2f', ax=ax)
ax.set_title('Correlation Matrix')
st.pyplot(fig)
plt.close(fig)
st.markdown("---")

# ============ Role & Career Stage Analysis ============
st.markdown("## 📊 Role & Career Stage Analysis")
col1, col2 = st.columns(2)

with col1:
    role_engagement = filtered_df.groupby('JobRole')['Engagement_Index'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 6))
    role_engagement.plot(kind='bar', ax=ax, color='steelblue')
    ax.set_xlabel('Job Role')
    ax.set_ylabel('Average Engagement Index')
    ax.set_title('Engagement by Job Role')
    ax.tick_params(axis='x', rotation=45, labelsize=8)
    st.pyplot(fig)
    plt.close(fig)

with col2:
    level_engagement = filtered_df.groupby('JobLevel')['Engagement_Index'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(level_engagement['JobLevel'], level_engagement['Engagement_Index'], marker='o', linestyle='-', color='#0066B3')
    ax.set_xlabel('Job Level')
    ax.set_ylabel('Engagement Index')
    ax.set_title('Engagement by Job Level')
    ax.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig)
    plt.close(fig)

st.markdown("### Tenure vs Engagement Trends")
tenure_agg = filtered_df.groupby('YearsAtCompany').agg({'Engagement_Index':'mean', 'Attrition':'mean'}).reset_index()
fig, ax1 = plt.subplots(figsize=(10, 5))
color = 'tab:blue'
ax1.set_xlabel('Years at Company')
ax1.set_ylabel('Engagement Index', color=color)
ax1.plot(tenure_agg['YearsAtCompany'], tenure_agg['Engagement_Index'], marker='o', color=color, label='Engagement')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Attrition Rate (%)', color=color)
ax2.plot(tenure_agg['YearsAtCompany'], tenure_agg['Attrition']*100, marker='s', linestyle='--', color=color, label='Attrition')
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()
ax1.set_title('Engagement and Attrition Trends by Tenure')
st.pyplot(fig)
plt.close(fig)
st.markdown("---")

# ============ Manager Action Panel ============
st.markdown("## 🎯 Manager Action Panel")
low_engagement = filtered_df[filtered_df['Engagement_Index'] < engagement_threshold]
high_burnout = filtered_df[filtered_df['Burnout_Risk'] == 'High Risk']
critical_employees = filtered_df[(filtered_df['Engagement_Index'] < engagement_threshold) & (filtered_df['Burnout_Risk'] == 'High Risk')]

col1, col2, col3 = st.columns(3)
with col1: st.markdown(f"""<div class="kpi-card" style="background-color:#FFF3F3;"><div class="metric-value" style="color:#FF4444;">{len(low_engagement)}</div><div class="metric-label">⚠️ Low Engagement</div><div style="font-size:0.8rem;">Index &lt; {engagement_threshold}</div></div>""", unsafe_allow_html=True)
with col2: st.markdown(f"""<div class="kpi-card" style="background-color:#FFF3F3;"><div class="metric-value" style="color:#FF4444;">{len(high_burnout)}</div><div class="metric-label">🔥 High Burnout Risk</div><div style="font-size:0.8rem;">Overtime + Poor WLB</div></div>""", unsafe_allow_html=True)
with col3: st.markdown(f"""<div class="kpi-card" style="background-color:#FFE8E8;"><div class="metric-value" style="color:#CC0000;">{len(critical_employees)}</div><div class="metric-label">🚨 Critical Priority</div><div style="font-size:0.8rem;">Low Engagement + High Burnout</div></div>""", unsafe_allow_html=True)

st.markdown("### 🚨 Priority Intervention List")
if len(critical_employees) > 0:
    priority_cols = ['Age','Department','JobRole','Engagement_Index','WorkLifeBalance','OverTime','YearsAtCompany']
    priority_df = critical_employees[priority_cols].sort_values('Engagement_Index')
    st.dataframe(priority_df.round(2), use_container_width=True, hide_index=True)
else:
    st.success("✅ No critical employees found! Great job maintaining employee engagement!")

st.markdown("### 📋 Department Action Recommendations")
dept_stats = filtered_df.groupby('Department').agg({
    'Engagement_Index':'mean','WorkLifeBalance':'mean',
    'Burnout_Risk': lambda x: (x == 'High Risk').mean()*100,
    'Attrition':'mean'
}).reset_index()
dept_stats.columns = ['Department','Avg Engagement','Avg WLB','Burnout Risk %','Attrition Rate']
dept_stats = dept_stats.round(2)

for _, row in dept_stats.iterrows():
    if row['Burnout Risk %'] > 30:
        st.warning(f"**{row['Department']}** - ⚠️ High Burnout Risk ({row['Burnout Risk %']:.0f}%)\n- Engagement: {row['Avg Engagement']:.2f} | WLB: {row['Avg WLB']:.2f} | Attrition: {row['Attrition Rate']*100:.0f}%\n- **Recommendation**: Review workload distribution and implement stress reduction programs")
    elif row['Avg Engagement'] < 2.8:
        st.info(f"**{row['Department']}** - 📉 Low Engagement ({row['Avg Engagement']:.2f})\n- Burnout Risk: {row['Burnout Risk %']:.0f}% | WLB: {row['Avg WLB']:.2f}\n- **Recommendation**: Improve job satisfaction through recognition programs and career development")
    else:
        st.success(f"**{row['Department']}** - ✅ Good Standing\n- Engagement: {row['Avg Engagement']:.2f} | Burnout Risk: {row['Burnout Risk %']:.0f}%\n- **Recommendation**: Continue monitoring engagement trends")

st.markdown("---")
st.markdown("""<div style="text-align: center; padding: 20px; color: #666; border-top: 1px solid #ddd;"><p>🏢 Palo Alto Networks | Employee Engagement & Burnout Diagnostic Dashboard</p><p style="font-size: 0.8rem;">Data-driven insights for proactive HR intervention</p></div>""", unsafe_allow_html=True)