# Mini Süreç Madenciliği Uygulaması Çalıştırma Rehberi (Google Colab)

Bu rehber, "Mini Süreç Madenciliği Uygulaması"nı Google Colab ortamında çalıştırmak için izlemeniz gereken adımları özetler.

## Ön Koşullar

1.  **Google Hesabı:** Google Colab'ı kullanmak için.
2.  **Ngrok Hesabı ve Authtoken:**
    *   Ngrok hesabı oluşturun: [https://ngrok.com/](https://ngrok.com/)
    *   Authtoken'ınızı buradan alın: [https://dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken) (Örn: `2xNMeNi3ZDYPDzZlvXXXXXXXXXX_XXXXXXXXXXXXXXXXX`)

## Çalıştırma Adımları

1.  **Ngrok Authtoken'ı Colab Secrets'a Ekleme:**
    *   Google Colab not defterinizi açın.
    *   Sol taraftaki menüden anahtar (🔑) simgesine tıklayarak "Secrets" bölümünü açın.
    *   "Add a new secret" (Yeni bir gizli anahtar ekle) butonuna tıklayın.
    *   **Name (Ad)** alanına `NGROK_AUTH_TOKEN` yazın.
    *   **Value (Değer)** alanına ngrok panonuzdan aldığınız authtoken'ı yapıştırın (örneğin, `2xNMeNi3ZDYPDzZlv32VXXZmlml_XXXXXXXXXXXXXXX`).
    *   "Notebook access" (Not defteri erişimi) seçeneğinin işaretli olduğundan emin olun ve kaydedin.

2.  **Yeni Bir Google Colab Not Defteri Oluşturun.**

3.  **Gerekli Kütüphaneleri Kurun:**
    *   Colab'da yeni bir kod hücresi oluşturun.
    *   Aşağıdaki komutu bu hücreye yapıştırın ve çalıştırın:
        ```python
        !pip install streamlit pyngrok pandas matplotlib seaborn networkx graphviz -q
        ```

4.  **Streamlit Uygulama Dosyasını (`app.py`) Oluşturun:**
    *   Colab'da yeni bir kod hücresi oluşturun.
    *   Size sağlanan **tüm `app.py` içeriğini** (yani `%%writefile app.py` ile başlayan ve tüm Streamlit Python kodunu içeren bloğu) bu hücreye yapıştırın ve çalıştırın.
    *   Bu işlem, Colab ortamınızda `app.py` adında bir dosya oluşturacaktır.

5.  **Streamlit Uygulamasını Başlatın ve Ngrok Tünelini Oluşturun:**
    *   Colab'da yeni bir kod hücresi oluşturun.
    *   Size sağlanan **Streamlit uygulamasını başlatma ve ngrok tünelini oluşturma kodunu** (yani `from pyngrok import ngrok, conf` ile başlayan ve `!streamlit run app.py ...` komutunu içeren bloğu) bu hücreye yapıştırın ve çalıştırın.
    *   Bu hücre, Colab Secrets'tan `NGROK_AUTH_TOKEN`'ınızı alacak, ngrok tünelini başlatacak ve Streamlit uygulamasını çalıştıracaktır.

6.  **Uygulamaya Erişin:**
    *   5. adımdaki hücre çalıştıktan sonra, çıktıda `Streamlit uygulamanız burada çalışıyor: https://xxxx-xx-xxx-xxx-xx.ngrok-free.app` gibi bir URL göreceksiniz.
    *   Bu URL'ye tıklayarak çalışan Streamlit uygulamasını tarayıcınızda açabilirsiniz.

## Giriş Veri Formatı

Uygulamanın doğru çalışabilmesi için yükleyeceğiniz `.csv` dosyası aşağıdaki sütunları içermelidir:
*   `Case ID`
*   `Activity Name`
*   `Start Time`
*   `End Time`

## Uygulamayı Durdurma

Uygulamayı ve ngrok tünelini durdurmak için Colab'da 5. adımdaki hücrenin çalışmasını durdurmanız yeterlidir.
