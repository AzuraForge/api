# AzuraForge API Servisi

Bu servis, AzuraForge platformunun merkezi iletişim katmanı ve dış dünyaya açılan ağ geçididir.

## 🎯 Ana Sorumluluklar

1.  **RESTful API Sunucusu:**
    *   `Dashboard` ve potansiyel diğer istemciler için standart HTTP endpoint'leri sağlar (`/experiments`, `/pipelines` vb.).
    *   Gelen istekleri doğrular ve işlenmesi için görevleri `Celery` kuyruğuna (Redis) iletir.

2.  **WebSocket Sunucusu:**
    *   Devam eden deneylerin durumunu (`/ws/task_status/{task_id}`) canlı olarak takip etmek için WebSocket bağlantıları sunar.

3.  **Redis Pub/Sub Dinleyicisi:**
    *   `Worker` tarafından yayınlanan ilerleme mesajlarını (`task-progress:*` kanalları) dinler ve bu mesajları ilgili WebSocket istemcisine anında iletir.

---

## 🏛️ Ekosistemdeki Yeri

Bu servis, AzuraForge ekosisteminin bir parçasıdır. Projenin genel mimarisini, vizyonunu ve geliştirme rehberini anlamak için lütfen ana **[AzuraForge Platform Dokümantasyonuna](https://github.com/AzuraForge/platform/tree/main/docs)** başvurun.

---

## 🛠️ Yerel Geliştirme ve Test

Bu servisi yerel ortamda çalıştırmak ve test etmek için, ana `platform` reposundaki **[Geliştirme Rehberi](https://github.com/AzuraForge/platform/blob/main/docs/DEVELOPMENT_GUIDE.md)**'ni takip ederek genel ortamı kurun.

Sanal ortam aktive edildikten sonra, bu repo dizinindeyken aşağıdaki komutla API sunucusunu başlatabilirsiniz:

```bash
# api/ kök dizinindeyken
start-api
```

Sunucu `http://localhost:8000` adresinde çalışmaya başlayacaktır. Birim testlerini çalıştırmak için `pytest` komutunu kullanın.
