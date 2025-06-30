# AzuraForge API Servisi

Bu servis, AzuraForge platformunun merkezi iletişim katmanı ve dış dünyaya açılan ağ geçididir.

## 🎯 Ana Sorumluluklar

1.  **RESTful API Sunucusu:**
    *   `Dashboard` ve potansiyel diğer istemciler için standart HTTP endpoint'leri sağlar (`/experiments`, `/pipelines` vb.).
    *   Gelen istekleri doğrular ve işlenmesi için görevleri `Celery` kuyruğuna (Redis) iletir.

2.  **WebSocket Sunucusu:**
    *   Devam eden deneylerin durumunu canlı olarak takip etmek için (`/ws/task_status/{task_id}`) WebSocket bağlantıları sunar.

3.  **Redis Pub/Sub Dinleyicisi:**
    *   `Worker` tarafından yayınlanan ilerleme mesajlarını (`task-progress:*` kanalları) dinler ve bu mesajları ilgili WebSocket istemcisine anında iletir.

## 🛠️ Yerel Geliştirme ve Test

Bu servisi yerel ortamda çalıştırmak ve test etmek için, ana `platform` reposundaki **[Geliştirme Rehberi](../../platform/docs/DEVELOPMENT_GUIDE.md)**'ni takip edin.

Servis bağımlılıkları kurulduktan ve sanal ortam aktive edildikten sonra, aşağıdaki komutla API sunucusunu başlatabilirsiniz:

```bash
# api/ kök dizinindeyken
start-api
```

Sunucu `http://localhost:8000` adresinde çalışmaya başlayacaktır.

**Birim Testleri (Yakında):**
Birim testlerini çalıştırmak için:
```bash
pytest
```
