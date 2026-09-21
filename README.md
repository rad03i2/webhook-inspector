# Webhook Inspector

A small, local-first webhook receiver, inspector, HMAC verifier, exporter, and replay tool for developers. It uses Python's standard library plus SQLite, so the installed application has no third-party runtime dependencies.

## English

### Why this exists
Webhook integrations are difficult to debug when payloads disappear into application logs. Webhook Inspector gives you a predictable local endpoint, stores each request for later inspection, and provides explicit tools for signature verification and controlled replay.

### Features
- Receives `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, and `HEAD` requests.
- Binds to `127.0.0.1:8787` by default; external exposure is opt-in.
- Stores timestamp, method, path, remote address, headers, and body in SQLite.
- 1 MiB request-body limit to avoid accidental unbounded captures.
- Lists and filters captures by exact path; detailed text or JSON view.
- Verifies `sha256=<hex>` / bare SHA-256 HMAC signatures and SHA-1 when explicitly selected.
- Reads signing secrets from environment variables, never command-line secret values.
- Replays a captured request to an explicit HTTP(S) destination while dropping hop-by-hop/host/length headers.
- Exports captures as JSONL with overwrite protection.
- Safe deletion and retention pruning require `--yes`.
- SQLite WAL mode and indexes for practical local history.

### Requirements
- Python 3.10 or newer
- No external service, account, API key, or runtime package is required

### Installation
```bash
git clone https://github.com/rad03i2/webhook-inspector.git
cd webhook-inspector
python -m pip install -e .
```

For development/testing:
```bash
python -m pip install -e . pytest
python -m pytest -q
```

### Quick start
Start the receiver:
```bash
webhook-inspector serve
```

Send a test request from another terminal:
```bash
curl -X POST http://127.0.0.1:8787/github \
  -H "Content-Type: application/json" \
  -d '{"event":"ping"}'
```

Inspect captures:
```bash
webhook-inspector list
webhook-inspector list --path /github
webhook-inspector show 1
webhook-inspector show 1 --json
```

Verify an HMAC signature without exposing the secret in shell history:
```bash
# Linux/macOS
export WEBHOOK_SECRET="your-local-test-secret"
webhook-inspector verify 1 --header X-Hub-Signature-256
```

PowerShell:
```powershell
$env:WEBHOOK_SECRET = "your-local-test-secret"
webhook-inspector verify 1 --header X-Hub-Signature-256
```

Replay and export:
```bash
webhook-inspector replay 1 http://127.0.0.1:9000/test
webhook-inspector export captures.jsonl --limit 100
webhook-inspector prune --keep 200 --yes
```

### Configuration
The default database is `~/.webhook-inspector/events.db`. Override it globally with `WEBHOOK_INSPECTOR_DB` or per command with `--db PATH`. `serve` accepts `--host` and `--port`; binding to a non-loopback address should only be done on a trusted, controlled network.

### Project structure
```text
src/webhook_inspector/
  core.py       SQLite storage, event model, HMAC verification
  server.py     threaded local HTTP receiver
  cli.py        command-line interface, replay and export
  __init__.py   package metadata
tests/          unit, CLI and HTTP integration tests
.github/workflows/ci.yml
```

### Testing and validation
The test suite covers HMAC verification, storage lifecycle, pruning, limits, CLI safeguards/export, and an actual loopback HTTP capture. GitHub Actions runs the suite on Python 3.10, 3.12, and 3.13 across Ubuntu, Windows, and macOS.

### Preview / screenshots
This is intentionally a terminal application. For a repository preview, capture two terminals side-by-side: `webhook-inspector serve` receiving a request and `webhook-inspector show <id> --json` displaying the stored event. Do not use real secrets or production payloads in screenshots.

### Security and privacy
Captured headers and bodies can contain sensitive information and are stored **unencrypted** on the local filesystem. The server is loopback-only by default. Signing secrets are accepted through environment variables. Replay is explicit and never automatic. See [SECURITY.md](SECURITY.md).

### Limitations
- No browser GUI or public webhook tunnel.
- No authentication/TLS server is built in; use a trusted reverse proxy if external exposure is required.
- SQLite data is not encrypted at rest.
- Maximum captured body size is 1 MiB.
- HMAC verification supports SHA-256 and legacy SHA-1 only; provider-specific timestamp/signature schemes are not automatically interpreted.
- Replay is a developer convenience, not an exact network-level reproduction: selected transport headers are deliberately removed.

### Optional roadmap
Potential future additions include provider-specific signature profiles, redacted export, event search, configurable retention, and an optional local read-only web UI. These are not implemented today.

### Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). Keep changes focused and include tests for new behavior.

### License
MIT — see [LICENSE](LICENSE).

### Author
**Radwan Abdulhadi Ahmed**  
**رضوان عبدالهادي أحمد**  
GitHub: **@rad03i2**

---

## العربية

### نظرة عامة
**Webhook Inspector** أداة محلية صغيرة للمطورين لاستقبال طلبات Webhook وحفظها وفحصها والتحقق من توقيع HMAC وإعادة إرسال الطلبات المحفوظة عند الحاجة. تعتمد على Python ومكتبتها القياسية وSQLite، ولا تحتاج إلى خدمة سحابية أو مفتاح API.

### لماذا المشروع؟
تصحيح تكاملات Webhook يصبح صعبًا عندما تختفي الحمولة داخل سجلات التطبيق. توفر الأداة عنوانًا محليًا واضحًا للاختبار، وتحفظ كل طلب للفحص اللاحق، وتفصل التحقق من التوقيع وإعادة الإرسال في أوامر صريحة وآمنة نسبيًا.

### الميزات
- استقبال `GET` و`POST` و`PUT` و`PATCH` و`DELETE` و`HEAD`.
- الاستماع افتراضيًا على `127.0.0.1:8787` فقط.
- حفظ الوقت والطريقة والمسار والعنوان البعيد والرؤوس والجسم في SQLite.
- حد أقصى 1 MiB لجسم الطلب.
- عرض السجلات والتصفية بالمسار وعرض التفاصيل كنص أو JSON.
- التحقق من توقيعات HMAC باستخدام SHA-256، مع SHA-1 عند اختياره صراحة.
- قراءة سر التوقيع من متغير بيئة بدل تمريره في سطر الأوامر.
- إعادة إرسال حدث محفوظ إلى عنوان HTTP/HTTPS يحدده المستخدم.
- تصدير JSONL مع منع الاستبدال غير المقصود.
- الحذف والتنظيف يتطلبان `--yes`.

### المتطلبات والتثبيت
تحتاج Python 3.10 أو أحدث فقط:
```bash
git clone https://github.com/rad03i2/webhook-inspector.git
cd webhook-inspector
python -m pip install -e .
```

للتطوير والاختبارات:
```bash
python -m pip install -e . pytest
python -m pytest -q
```

### الاستخدام
شغّل المستقبل:
```bash
webhook-inspector serve
```

ثم أرسل طلبًا تجريبيًا:
```bash
curl -X POST http://127.0.0.1:8787/github -H "Content-Type: application/json" -d '{"event":"ping"}'
```

الفحص والإدارة:
```bash
webhook-inspector list
webhook-inspector show 1 --json
webhook-inspector export captures.jsonl
webhook-inspector replay 1 http://127.0.0.1:9000/test
webhook-inspector prune --keep 200 --yes
```

للتحقق من التوقيع، ضع السر في `WEBHOOK_SECRET` ثم نفّذ:
```bash
webhook-inspector verify 1 --header X-Hub-Signature-256
```

### الإعداد
قاعدة البيانات الافتراضية هي `~/.webhook-inspector/events.db`. يمكن تغييرها عبر `WEBHOOK_INSPECTOR_DB` أو الخيار `--db`. ويمكن تغيير المضيف والمنفذ في أمر `serve`، لكن لا يُنصح بالاستماع على واجهة شبكة عامة دون Reverse Proxy موثوق وضوابط شبكة مناسبة.

### بنية المشروع
- `core.py`: نموذج الحدث والتخزين والتحقق من HMAC.
- `server.py`: مستقبل HTTP محلي متعدد الخيوط.
- `cli.py`: الأوامر والتصدير وإعادة الإرسال.
- `tests/`: اختبارات الوحدة وCLI واختبار تكامل HTTP فعلي على loopback.
- `.github/workflows/ci.yml`: اختبارات آلية متعددة الأنظمة وإصدارات Python.

### الاختبارات والمعاينة
تغطي الاختبارات التوقيع والتخزين والحذف والتنظيف والحدود وحماية CLI والتصدير واستقبال HTTP فعليًا. ولصورة معاينة للمستودع، يمكن عرض نافذتي Terminal جنبًا إلى جنب: الأولى تشغّل `serve` والثانية تعرض حدثًا تجريبيًا عبر `show --json`، دون استخدام بيانات أو أسرار حقيقية.

### الخصوصية والأمان
قد تحتوي الرؤوس والأجسام الملتقطة على معلومات حساسة، وهي محفوظة محليًا **بدون تشفير**. الاستماع محلي افتراضيًا، وإعادة الإرسال لا تحدث تلقائيًا، والأسرار تُقرأ من متغيرات البيئة. راجع [SECURITY.md](SECURITY.md).

### القيود
لا توجد واجهة ويب أو نفق عام أو TLS/مصادقة مدمجان. البيانات غير مشفرة، وحجم الجسم محدود بـ1 MiB. التحقق يدعم SHA-256 وSHA-1 العامين وليس كل مخططات التوقيع الخاصة بالمزودين. كما أن Replay يحذف بعض رؤوس النقل عمدًا، لذلك ليس نسخة شبكية حرفية من الطلب الأصلي.

### تطوير اختياري
يمكن مستقبلًا إضافة ملفات تعريف لتواقيع المزودين، وتصدير مع إخفاء البيانات الحساسة، وبحث متقدم، وسياسة احتفاظ قابلة للضبط، وواجهة ويب محلية للقراءة فقط. هذه الميزات غير منفذة حاليًا.

### المساهمة والترخيص
راجع [CONTRIBUTING.md](CONTRIBUTING.md). المشروع مرخص وفق MIT؛ راجع [LICENSE](LICENSE).

### المؤلف
**Radwan Abdulhadi Ahmed**  
**رضوان عبدالهادي أحمد**  
GitHub: **@rad03i2**
