!pip install streamlit pyngrok -q

%%writefile app.py
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import graphviz
from io import BytesIO
import warnings

# Olası uyarıları bastırmak için (isteğe bağlı)
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', category=FutureWarning)

# Streamlit sayfa konfigürasyonu
st.set_page_config(layout="wide", page_title="Mini Süreç Madenciliği")

# --- Veri İşleme ve Analiz Fonksiyonları ---
def load_and_process_data(uploaded_file_content):
    """Veriyi yükler, temel kontrolleri ve ön işlemeyi yapar."""
    try:
        df = pd.read_csv(BytesIO(uploaded_file_content))

        required_columns = ['Case ID', 'Activity Name', 'Start Time', 'End Time']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"CSV dosyasında eksik sütun(lar) var: {', '.join(missing_cols)}. "
                     f"Lütfen dosyanın '{', '.join(required_columns)}' sütunlarını içerdiğinden emin olun.")
            return None

        try:
            df['Start Time'] = pd.to_datetime(df['Start Time'])
            df['End Time'] = pd.to_datetime(df['End Time'])
        except Exception as e:
            st.error(f"Tarih/saat sütunları ('Start Time', 'End Time') dönüştürülürken hata oluştu: {e}. "
                     "Lütfen tarih formatlarını kontrol edin.")
            return None

        df['Duration'] = (df['End Time'] - df['Start Time']).dt.total_seconds() / 60
        if (df['Duration'] < 0).any():
            st.warning("Uyarı: Bazı aktiviteler için hesaplanan süre negatif. 'Start Time' ve 'End Time' değerlerini kontrol edin.")

        # Session state'e df'i ve işlem durumunu kaydet
        st.session_state.df = df
        st.session_state.data_processed = True
        return df
    except Exception as e:
        st.error(f"Dosya okunurken veya işlenirken bir hata oluştu: {e}")
        st.session_state.data_processed = False
        return None

def calculate_case_durations(df):
    """Her case'in toplam süresini hesaplar."""
    if df is None or 'Duration' not in df.columns: return None
    case_durations = df.groupby("Case ID")['Duration'].sum().reset_index()
    case_durations.columns = ["Case ID", "Toplam Süre (dakika)"]
    return case_durations

def calculate_activity_counts(df):
    """Adım frekanslarını hesaplar."""
    if df is None: return None
    activity_counts = df['Activity Name'].value_counts().reset_index()
    activity_counts.columns = ['Activity Name', 'Frekans']
    return activity_counts

def calculate_average_completion_time(case_durations_df):
    """Ortalama süreç tamamlanma süresini hesaplar."""
    if case_durations_df is None or case_durations_df.empty: return None
    return case_durations_df['Toplam Süre (dakika)'].mean()

def calculate_transitions(df):
    """Adım geçiş frekanslarını hesaplar."""
    if df is None: return None
    df_sorted = df.sort_values(['Case ID', 'Start Time'])
    df_sorted['Next Activity'] = df_sorted.groupby('Case ID')['Activity Name'].shift(-1)
    transitions = df_sorted.groupby(['Activity Name', 'Next Activity'], dropna=True).size().reset_index(name='Count')
    return transitions.sort_values('Count', ascending=False)

# --- Görselleştirme Fonksiyonları ---
def plot_activity_frequency_chart(activity_counts_df):
    """Adım frekanslarını bar chart olarak çizer."""
    if activity_counts_df is None or activity_counts_df.empty:
        st.info("Adım frekansları verisi bulunamadı.")
        return None

    fig, ax = plt.subplots(figsize=(10, 8))
    data_to_plot = activity_counts_df.head(15)
    sns.barplot(x='Frekans', y='Activity Name', data=data_to_plot, palette="viridis", orient='h', ax=ax)
    ax.set_xlabel("Frekans")
    ax.set_ylabel("Aktivite Adı")
    ax.set_title("En Sık Gerçekleşen İlk 15 Aktivite")
    plt.tight_layout()
    return fig

def plot_networkx_graph(transitions_df):
    """NetworkX ile süreç geçiş diyagramı çizer."""
    if transitions_df is None or transitions_df.empty:
        st.info("NetworkX grafiği için geçiş verisi bulunamadı.")
        return None

    G = nx.DiGraph()
    transitions_for_graph = transitions_df.head(20) # En sık ilk 20 geçiş

    if transitions_for_graph.empty:
        st.info("NetworkX grafiği için çizilecek geçiş bulunamadı.")
        return None

    for _, row in transitions_for_graph.iterrows():
        G.add_edge(str(row['Activity Name']), str(row['Next Activity']), weight=row['Count'])

    if G.number_of_nodes() == 0:
        st.info("NetworkX grafiği için yeterli node bulunamadı.")
        return None

    fig, ax = plt.subplots(figsize=(14, 10))
    pos = nx.spring_layout(G, k=0.9, iterations=50, seed=42, scale=2.0)
    node_sizes = [G.degree(node) * 300 + 1000 for node in G.nodes()] if G.nodes() else 2000
    edge_widths = [(d['weight'] / (transitions_for_graph['Count'].max() or 1) * 4) + 1 for u, v, d in G.edges(data=True)] if G.edges() else 1

    nx.draw(G, pos, ax=ax, with_labels=True, node_color='skyblue', node_size=node_sizes,
            edge_color='gray', font_size=9, font_weight='bold', arrows=True,
            arrowstyle='-|>', arrowsize=15, width=edge_widths)

    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, ax=ax, edge_labels=edge_labels, font_size=8, font_color='darkred')
    ax.set_title("Süreç Akış Ağı (En Sık 20 Geçiş)")
    return fig

def create_graphviz_dot(transitions_df):
    """Graphviz DOT nesnesini oluşturur."""
    if transitions_df is None or transitions_df.empty:
        st.info("Graphviz diyagramı için geçiş verisi bulunamadı.")
        return None

    dot = graphviz.Digraph(comment='Süreç Akışı', engine='dot')
    dot.attr(rankdir='LR', size='15,10!', splines='curved', nodesep='0.7', ranksep='1.0', overlap='false') # Boyut ve overlap ayarı
    dot.attr('node', shape='box', style='filled', fillcolor='lightblue', fontname='Helvetica', fontsize='10')
    dot.attr('edge', fontname='Helvetica', fontsize='8', color='dimgray', arrowsize='0.7')

    transitions_for_gv = transitions_df.head(30) # En sık ilk 30 geçiş
    if transitions_for_gv.empty:
        st.info("Graphviz diyagramı için çizilecek geçiş bulunamadı.")
        return None

    all_activities = pd.concat([transitions_for_gv['Activity Name'], transitions_for_gv['Next Activity']]).unique()
    for activity in all_activities:
        dot.node(str(activity))

    min_count = transitions_for_gv['Count'].min()
    max_count = transitions_for_gv['Count'].max() if not transitions_for_gv.empty else 1 # ZeroDivision önle

    for _, row in transitions_for_gv.iterrows():
        src, tgt, freq = str(row['Activity Name']), str(row['Next Activity']), int(row['Count'])
        penwidth_val = 1.0
        if max_count > min_count and max_count != min_count: # ZeroDivisionError ve sabit kalınlık önlemi
             penwidth_val = 1.0 + 4.0 * (freq - min_count) / (max_count - min_count)
        dot.edge(src, tgt, label=f" {freq} ", penwidth=str(round(penwidth_val, 2)))
    return dot

# --- Streamlit Arayüzü ---
st.title("🚀 Mini Süreç Madenciliği Uygulaması")

# Session state başlatma (eğer yoksa)
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False
    st.session_state.df = None
    st.session_state.case_durations = None
    st.session_state.activity_counts = None
    st.session_state.avg_completion_time = None
    st.session_state.transitions = None

# Dosya yükleyici
uploaded_file = st.file_uploader("📂 Bir .csv süreç log dosyası yükleyin (Sürükle & Bırak Destekli)", type="csv")

if uploaded_file is not None:
    if "current_file_name" not in st.session_state or st.session_state.current_file_name != uploaded_file.name:
        st.session_state.current_file_name = uploaded_file.name
        st.session_state.data_processed = False
        st.session_state.df = None

    if not st.session_state.data_processed:
        with st.spinner('Veri işleniyor... Lütfen bekleyin.'):
            file_content = uploaded_file.getvalue()
            df_loaded = load_and_process_data(file_content)
            if df_loaded is not None:
                st.session_state.case_durations = calculate_case_durations(df_loaded)
                st.session_state.activity_counts = calculate_activity_counts(df_loaded)
                st.session_state.avg_completion_time = calculate_average_completion_time(st.session_state.case_durations)
                st.session_state.transitions = calculate_transitions(df_loaded)
                st.success("Veri başarıyla işlendi! Analizleri görmek için kenar çubuğunu kullanın.")
            else:
                st.error("Veri işlenemedi. Lütfen dosyanızı kontrol edin ve tekrar deneyin.")
else:
    st.info("Lütfen analiz etmek için bir CSV dosyası yükleyin.")
    if st.session_state.data_processed:
        st.session_state.data_processed = False
        st.session_state.df = None
        st.session_state.case_durations = None
        st.session_state.activity_counts = None
        st.session_state.avg_completion_time = None
        st.session_state.transitions = None

st.sidebar.title("📜 Analiz Sayfaları")
page_options = [
    "Giriş & Ham Veri",
    "Case Süreleri",
    "Adım Frekansları",
    "Ortalama Süreç Süresi",
    "Adım Geçişleri",
    "Adım Frekansı Grafiği",
    "Süreç Ağı (NetworkX)",
    "Süreç Akış Diyagramı (Graphviz)"
]

if st.session_state.data_processed and st.session_state.df is not None:
    selected_page = st.sidebar.radio("Gitmek istediğiniz sayfa:", page_options)

    if selected_page == "Giriş & Ham Veri":
        st.header("📊 Ham Veri (İlk 20 Satır)")
        if st.session_state.df is not None:
            st.dataframe(st.session_state.df.head(20))
            st.markdown(f"Toplam {len(st.session_state.df)} satır veri yüklendi.")
        else:
            st.info("Görüntülenecek ham veri yok.")

    elif selected_page == "Case Süreleri":
        st.header("⏱️ Her Case'in Toplam Süresi")
        if st.session_state.case_durations is not None:
            st.dataframe(st.session_state.case_durations)
        else:
            st.info("Görüntülenecek case süresi verisi yok.")

    elif selected_page == "Adım Frekansları":
        st.header("📌 En Sık Gerçekleşen Adımlar")
        if st.session_state.activity_counts is not None:
            st.dataframe(st.session_state.activity_counts)
        else:
            st.info("Görüntülenecek adım frekansı verisi yok.")

    elif selected_page == "Ortalama Süreç Süresi":
        st.header("📈 Ortalama Süreç Tamamlanma Süresi")
        if st.session_state.avg_completion_time is not None:
            st.success(f"Ortalama süreç tamamlanma süresi: {st.session_state.avg_completion_time:.2f} dakika")
        else:
            st.info("Ortalama süreç süresi hesaplanamadı.")

    elif selected_page == "Adım Geçişleri":
        st.header("🔁 En Sık Adım Geçişleri (İlk 20)")
        if st.session_state.transitions is not None:
            st.dataframe(st.session_state.transitions.head(20))
        else:
            st.info("Görüntülenecek adım geçiş verisi yok.")

    elif selected_page == "Adım Frekansı Grafiği":
        st.header("📊 Adım Frekansları (Bar Chart)")
        if st.session_state.activity_counts is not None:
            fig = plot_activity_frequency_chart(st.session_state.activity_counts)
            if fig:
                st.pyplot(fig)
                plt.clf()
        else:
            st.info("Grafik için adım frekansı verisi yok.")

    elif selected_page == "Süreç Ağı (NetworkX)":
        st.header("🕸️ Süreç Geçiş Diyagramı (NetworkX)")
        if st.session_state.transitions is not None:
            with st.spinner("NetworkX grafiği oluşturuluyor..."):
                fig = plot_networkx_graph(st.session_state.transitions)
                if fig:
                    st.pyplot(fig)
                    plt.clf()
        else:
            st.info("Grafik için geçiş verisi yok.")

    elif selected_page == "Süreç Akış Diyagramı (Graphviz)":
        st.header("🗺️ BPMN Benzeri Akış Diyagramı (Graphviz)")
        if st.session_state.transitions is not None:
            with st.spinner("Graphviz diyagramı oluşturuluyor..."):
                dot_obj = create_graphviz_dot(st.session_state.transitions)
                if dot_obj:
                    try:
                        st.graphviz_chart(dot_obj)
                    except graphviz.backend.execute.ExecutableNotFound:
                        st.error("Graphviz bulunamadı. Lütfen sisteminize Graphviz'i kurun ve PATH'e ekleyin.")
                    except Exception as e_gv:
                         st.error(f"Graphviz diyagramı oluşturulurken bir hata oluştu: {e_gv}")
        else:
            st.info("Diyagram için geçiş verisi yok.")
else:
    if uploaded_file:
        st.sidebar.warning("Veri işlenemedi. Lütfen yukarıdaki hata mesajlarını kontrol edin.")
    else:
        st.sidebar.info("Analizleri görmek için lütfen bir CSV dosyası yükleyin.")

st.sidebar.markdown("---")
st.sidebar.info("Mini Süreç Madenciliği Uygulaması v2.0")
