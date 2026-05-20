"""
Модуль 3: ML-анализ аномалий
"""

import streamlit as st
from modules.session_data import ensure_session_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ML-анализ аномалий", page_icon=None, layout="wide")
ensure_session_data()

# Кастомный CSS для фиолетового дизайна
st.markdown("""
<style>
    h1, h2, h3, h4 {
        color: #3c096c !important;
        font-family: 'Outfit', 'Inter', sans-serif !important;
        font-weight: 800 !important;
    }
    hr {
        border-color: #ebdfff !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #5a189a !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: #7b2cbf !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05rem !important;
    }
    [data-testid="stMetric"] {
        background-color: #fcfaff !important;
        border: 1px solid #ebdfff !important;
        border-left: 5px solid #7b2cbf !important;
        border-radius: 10px !important;
        padding: 0.8rem 1rem !important;
        box-shadow: 0 4px 12px rgba(123, 44, 191, 0.03) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# ML Anomaly Detector")

st.markdown("""
Машинное обучение для выявления аномалий и анализа паттернов в транзакциях
""")

# Получаем данные
accounts_df = st.session_state.accounts_df
transactions_df = st.session_state.transactions_df

# Импортируем модули
from modules.ml_analyzer import MLAnalyzer
from modules.ml_model_saver import MLModelSaver

# Инициализируем saver
model_saver = MLModelSaver()

# Проверяем есть ли сохраненная модель
if model_saver.model_exists():
    with st.spinner("Загрузка моделей машинного обучения..."):
        ml_analyzer = model_saver.create_ml_analyzer_from_saved(transactions_df, accounts_df)
    st.toast("✅ Модели машинного обучения успешно загружены!", icon="🤖")
else:
    st.markdown("""
    <div style="background-color: #fff9db; border-left: 5px solid #fab005; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #664d03; font-weight: 500;">
        Обучение моделей машинного обучения запущено в первый раз
    </div>
    """, unsafe_allow_html=True)
    with st.spinner("Обучение моделей..."):
        ml_analyzer = MLAnalyzer(transactions_df, accounts_df)
        model_saver.save_models(ml_analyzer)
    st.toast("🎉 Модели успешно обучены и сохранены!", icon="🚀")

# ВКЛАДКИ
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Аномалии",
    "Паттерны",
    "Предсказания",
    "Тренды",
    "Рил тайм"
])

with tab1:
    st.markdown("### Выявление аномальных транзакций")
    
    days_to_check = st.slider("Анализировать последние N дней:", 7, 90, 30)
    
    anomalies_df = ml_analyzer.detect_anomalies(recent_days=days_to_check)
    
    if len(anomalies_df) > 0:
        st.markdown(f"""
        <div style="background-color: #fff0f3; border-left: 5px solid #ff4d6d; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #c9184a; font-weight: 500;">
            ⚠️ Обнаружено {len(anomalies_df)} аномальных транзакций за последние {days_to_check} дней.
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Сумма аномалий", f"${anomalies_df['amount'].sum():,.0f}")
        
        with col2:
            anomaly_pct = (len(anomalies_df) / len(transactions_df)) * 100
            st.metric("% от всех", f"{anomaly_pct:.2f}%")
        
        with col3:
            most_common = anomalies_df['anomaly_type'].mode()[0] if len(anomalies_df) > 0 else "N/A"
            st.metric("Основной тип", most_common)
        
        # Таблица
        display_anomalies = anomalies_df.copy()
        display_anomalies['amount'] = display_anomalies['amount'].apply(lambda x: f"${x:,.2f}")
        display_anomalies['datetime'] = display_anomalies['datetime'].dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            display_anomalies[[
                'transaction_id', 'datetime', 'type', 'amount',
                'currency', 'anomaly_type'
            ]],
            hide_index=True,
            use_container_width=True
        )
        
        # График
        fig_anomalies = px.scatter(
            anomalies_df,
            x='datetime',
            y='amount',
            color='anomaly_type',
            size='amount',
            title="Аномальные транзакции",
            hover_data=['transaction_id'],
            color_discrete_sequence=['#7b2cbf', '#ff4d6d', '#3c096c', '#c77dff']
        )
        
        fig_anomalies.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
            title_font=dict(size=14, color="#3c096c", family="Outfit, Inter, sans-serif"),
            xaxis=dict(showgrid=False, linecolor='#ebdfff', title="Дата"),
            yaxis=dict(showgrid=True, gridcolor='#f3eeff', linecolor='#ebdfff', title="Сумма ($)")
        )
        st.plotly_chart(fig_anomalies, use_container_width=True)
    else:
        st.markdown(f"""
        <div style="background-color: #f4fbf7; border-left: 5px solid #2b8a3e; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #2b8a3e; font-weight: 600;">
            ✅ Аномалий не обнаружено за последние {days_to_check} дней!
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### Анализ паттернов")
    
    patterns = ml_analyzer.analyze_transaction_patterns()
    
    # Паттерн по часам
    st.markdown("#### Активность по часам суток")
    
    fig_hourly = px.line(
        patterns['hourly'],
        x='hour',
        y='num_transactions',
        title="Количество транзакций по часам",
        markers=True
    )
    
    fig_hourly.update_traces(line=dict(color='#7b2cbf', width=2), marker=dict(color='#3c096c'))
    
    fig_hourly.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
        title_font=dict(size=14, color="#3c096c", family="Outfit, Inter, sans-serif"),
        xaxis=dict(showgrid=False, linecolor='#ebdfff', title="Час суток"),
        yaxis=dict(showgrid=True, gridcolor='#f3eeff', linecolor='#ebdfff', title="Количество транзакций")
    )
    st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Паттерн по дням
    st.markdown("#### Активность по дням недели")
    
    fig_weekday = px.bar(
        patterns['weekday'],
        x='day_name',
        y='num_transactions',
        color='total_amount',
        title="Транзакции по дням недели",
        color_continuous_scale=['#f3eeff', '#c77dff', '#7b2cbf', '#3c096c']
    )
    
    fig_weekday.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
        title_font=dict(size=14, color="#3c096c", family="Outfit, Inter, sans-serif"),
        xaxis=dict(showgrid=False, linecolor='#ebdfff', title="День недели"),
        yaxis=dict(showgrid=True, gridcolor='#f3eeff', linecolor='#ebdfff', title="Количество транзакций")
    )
    st.plotly_chart(fig_weekday, use_container_width=True)
    
    # Паттерны по типам и валютам
    col1, col2 = st.columns(2)
    
    with col1:
        fig_types = px.pie(
            patterns['type'],
            values='num_transactions',
            names='type',
            title="Типы транзакций",
            color_discrete_sequence=['#7b2cbf', '#c77dff', '#3c096c', '#ff4d6d']
        )
        fig_types.update_layout(
            font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
            title_font=dict(size=14, color="#3c096c", family="Outfit, Inter, sans-serif")
        )
        st.plotly_chart(fig_types, use_container_width=True)
    
    with col2:
        fig_currency = px.pie(
            patterns['currency'],
            values='total_amount',
            names='currency',
            title="Объем по валютам",
            color_discrete_sequence=['#3c096c', '#7b2cbf', '#c77dff', '#ebdfff']
        )
        fig_currency.update_layout(
            font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
            title_font=dict(size=14, color="#3c096c", family="Outfit, Inter, sans-serif")
        )
        st.plotly_chart(fig_currency, use_container_width=True)

with tab3:
    st.markdown("### ML-предсказания объемов")
    
    accuracy_info = ml_analyzer.calculate_prediction_accuracy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Точность модели",
            f"{accuracy_info['accuracy']:.1f}%"
        )
    
    with col2:
        st.metric(
            "Средняя ошибка",
            f"${accuracy_info['mean_absolute_error']:,.0f}"
        )
    
    # Прогноз
    predictions_df = ml_analyzer.predict_future_volumes(days_ahead=30)
    
    fig_predictions = px.line(
        predictions_df,
        x='date',
        y='predicted_volume',
        title="Предсказанный объем транзакций на 30 дней",
        markers=True
    )
    
    fig_predictions.update_traces(line=dict(color='#7b2cbf', width=2), marker=dict(color='#3c096c'))
    
    fig_predictions.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
        title_font=dict(size=14, color="#3c096c", family="Outfit, Inter, sans-serif"),
        xaxis=dict(showgrid=False, linecolor='#ebdfff', title="Дата"),
        yaxis=dict(showgrid=True, gridcolor='#f3eeff', linecolor='#ebdfff', title="Предсказанный объем ($)")
    )
    st.plotly_chart(fig_predictions, use_container_width=True)

with tab4:
    st.markdown("### Анализ изменений трендов")
    
    trend_changes = ml_analyzer.detect_trend_changes(window_days=7)
    
    if len(trend_changes) > 0:
        st.markdown(f"""
        <div style="background-color: #fff9db; border-left: 5px solid #fab005; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #664d03; font-weight: 500;">
            ⚠️ Выявлено {len(trend_changes)} значительных изменений в трендах транзакций.
        </div>
        """, unsafe_allow_html=True)
        
        display_trends = trend_changes.copy()
        display_trends['amount_change'] = display_trends['amount_change'].apply(lambda x: f"{x:+.1f}%")
        display_trends['count_change'] = display_trends['count_change'].apply(lambda x: f"{x:+.1f}%")
        
        st.dataframe(display_trends, hide_index=True, use_container_width=True)
        
        fig_trends = px.scatter(
            trend_changes,
            x='date',
            y='amount_change',
            size='total_amount',
            color='trend',
            title="Изменения трендов",
            color_discrete_map={'Резкий рост': '#7b2cbf', 'Резкий спад': '#ff4d6d'}
        )
        
        fig_trends.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Outfit, Inter, sans-serif", color="#3c096c"),
            title_font=dict(size=14, color="#3c096c", family="Outfit, Inter, sans-serif"),
            xaxis=dict(showgrid=False, linecolor='#ebdfff', title="Дата"),
            yaxis=dict(showgrid=True, gridcolor='#f3eeff', linecolor='#ebdfff', title="Изменение объема (%)")
        )
        st.plotly_chart(fig_trends, use_container_width=True)
    else:
        st.markdown("""
        <div style="background-color: #f4fbf7; border-left: 5px solid #2b8a3e; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #2b8a3e; font-weight: 600;">
            ✅ Значительных изменений трендов не обнаружено!
        </div>
        """, unsafe_allow_html=True)

with tab5:
    st.markdown("### Мониторинг в реальном времени")
    st.markdown("(данные обновляются при действиях в системе)")
    
    realtime_status = ml_analyzer.detect_unusual_patterns_realtime()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Объем за 24 часа",
            f"${realtime_status.get('last_24h_volume', 0):,.0f}"
        )
    
    with col2:
        st.metric(
            "Транзакций за 24 часа",
            f"{realtime_status.get('last_24h_count', 0):,}"
        )
    
    if realtime_status['alerts']:
        st.markdown("### Обнаруженные проблемы")
        
        for alert in realtime_status['alerts']:
            if alert['severity'] == 'WARNING':
                st.markdown(f"""
                <div style="background-color: #fbf8ff; border-left: 5px solid #c77dff; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #7b2cbf; font-weight: 500;">
                    ⚠️ {alert['message']}
                </div>
                """, unsafe_allow_html=True)
            elif alert['severity'] == 'CRITICAL':
                st.markdown(f"""
                <div style="background-color: #fff0f3; border-left: 5px solid #ff4d6d; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #c9184a; font-weight: 500;">
                    🔴 {alert['message']}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #f4fbf7; border-left: 5px solid #2b8a3e; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; color: #2b8a3e; font-weight: 600;">
            ✅ Отклонений от нормы в реальном времени не обнаружено.
        </div>
        """, unsafe_allow_html=True)