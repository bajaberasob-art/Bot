import { useState } from "react";
import "./_group.css";

type Service = {
  title: string;
  description: string;
  icon: string;
  target: string;
};

const services: Service[] = [
  { title: "إدارة النظام", description: "إعدادات البوت وملفات السيرفر", icon: "✦", target: "النظام" },
  { title: "التقارير", description: "التحليلات والإحصائيات", icon: "▥", target: "التقارير" },
  { title: "الحماية", description: "جدار الحماية والفحص", icon: "◈", target: "الحماية" },
  { title: "الإعدادات", description: "تخصيص النظام", icon: "≡", target: "الإعدادات" },
];

const activities = [
  { title: "تم تحديث إعدادات الحماية", detail: "تغيير سياسة الدخول الآمن", time: "منذ 4 دقائق", tone: "" },
  { title: "تم تسجيل عضو جديد", detail: "انضمام إلى مجتمع PR1ME TEAM", time: "منذ 18 دقيقة", tone: "" },
  { title: "محاولة دخول مرفوضة", detail: "تم حظر الطلب تلقائياً", time: "منذ 32 دقيقة", tone: "red" },
  { title: "اكتملت مزامنة البيانات", detail: "تم تحديث مؤشرات السيرفر", time: "منذ ساعة", tone: "" },
];

const health = [
  ["خادم التطبيقات", "يعمل بشكل طبيعي"],
  ["قاعدة البيانات", "الحفظ والمزامنة يعملان"],
  ["خدمة الحماية", "مراقبة فعّالة"],
];

export function Current() {
  const [activeView, setActiveView] = useState("الرئيسية");
  const [selectedService, setSelectedService] = useState<string | null>(null);

  const goTo = (view: string) => {
    setActiveView(view);
    setSelectedService(view === "الرئيسية" ? null : view);
  };

  return (
    <main className="prime-preview">
      <div className="prime-shell">
        <header className="prime-topbar">
          <div className="prime-brand">
            <span className="prime-brand-mark" aria-hidden="true">P1</span>
            <div>
              <strong>PR1ME TEAM</strong>
              <small>CONTROL CENTER</small>
            </div>
          </div>
          <span className="prime-preview-badge">وضع المعاينة</span>
        </header>

        <section className="prime-hero" aria-labelledby="prime-preview-title">
          <div className="prime-hero-art" aria-hidden="true" />
          <div className="prime-hero-copy">
            <div className="prime-eyebrow">PR1ME TEAM / CONTROL CENTER</div>
            <h1 id="prime-preview-title">
              {selectedService ? `قسم ${selectedService}` : "كل شيء تحت السيطرة."}
            </h1>
            <p>
              مراقبة، حماية، أداء مستمر — نظامك يعمل بكفاءة وأمان.
              هذه نسخة عرض مستقلة ببيانات تجريبية فقط.
            </p>
            <div className="prime-hero-meta">
              <span className="prime-status-pulse" aria-hidden="true" />
              <span>النظام نشط</span>
              <small>آخر تحديث: الآن</small>
            </div>
          </div>
          <div className="prime-hero-status">
            <span className="prime-shield" aria-hidden="true" />
            <div>
              <strong>آمن ومتصل</strong>
              <small>1,284 عضو متصل</small>
            </div>
          </div>
        </section>

        <section className="prime-metrics" aria-label="مؤشرات النظام">
          <Metric icon="•" label="المستخدمون النشطون" value="1,284" detail="مستخدم" tone="blue" />
          <Metric icon="◈" label="الحوادث الأمنية" value="03" detail="تحتاج مراجعة" tone="red" />
          <Metric icon="▣" label="الأجهزة المتصلة" value="842" detail="جهاز متصل" tone="purple" />
          <Metric icon="✓" label="حالة النظام" value="آمن" detail="لا توجد تهديدات" tone="green" />
        </section>

        <section className="prime-panel prime-services">
          <div className="prime-panel-heading">
            <h2>الخدمات الرئيسية</h2>
            <button className="prime-text-link" type="button" onClick={() => goTo("الإعدادات")}>
              عرض الكل
            </button>
          </div>
          <div className="prime-service-list">
            {services.map((service) => (
              <button
                className="prime-service-row"
                type="button"
                key={service.title}
                onClick={() => goTo(service.target)}
              >
                <span className="prime-service-icon" aria-hidden="true">{service.icon}</span>
                <span>
                  <strong>{service.title}</strong>
                  <small>{service.description}</small>
                </span>
                <span className="prime-service-chevron" aria-hidden="true">‹</span>
              </button>
            ))}
          </div>
          {selectedService && (
            <div className="prime-notice" role="status">
              معاينة محلية: تم اختيار «{selectedService}». لا يتم حفظ أي تغيير ولا يتم الاتصال بالسيرفر الحقيقي.
            </div>
          )}
        </section>

        <div className="prime-lower-grid">
          <section className="prime-panel">
            <div className="prime-panel-heading">
              <h2>أحدث الأنشطة</h2>
              <button className="prime-text-link" type="button" onClick={() => goTo("التقارير")}>
                عرض الكل
              </button>
            </div>
            <div>
              {activities.map((activity) => (
                <div className="prime-activity-row" key={activity.title}>
                  <span className={`prime-activity-icon ${activity.tone}`} aria-hidden="true" />
                  <div>
                    <strong>{activity.title}</strong>
                    <small>{activity.detail}</small>
                  </div>
                  <time>{activity.time}</time>
                </div>
              ))}
            </div>
          </section>

          <section className="prime-panel">
            <div className="prime-panel-heading">
              <h2>حالة الخدمات</h2>
            </div>
            <div className="prime-health-list">
              {health.map(([title, detail]) => (
                <div className="prime-health-row" key={title}>
                  <span className="prime-health-icon" aria-hidden="true" />
                  <div>
                    <strong>{title}</strong>
                    <small>{detail}</small>
                  </div>
                  <span className="prime-health-state">طبيعي</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>

      <nav className="prime-bottom-nav" aria-label="التنقل التجريبي">
        {[
          ["الرئيسية", "⌂"],
          ["التقارير", "▥"],
          ["الحماية", "◈"],
          ["الإعدادات", "≡"],
        ].map(([label, icon]) => (
          <button
            className={activeView === label ? "active" : ""}
            type="button"
            key={label}
            onClick={() => goTo(label)}
          >
            <span aria-hidden="true">{icon}</span>
            {label}
          </button>
        ))}
      </nav>
    </main>
  );
}

function Metric({
  icon,
  label,
  value,
  detail,
  tone,
}: {
  icon: string;
  label: string;
  value: string;
  detail: string;
  tone: "blue" | "red" | "purple" | "green";
}) {
  return (
    <article className={`prime-metric prime-metric-${tone}`} data-icon={icon}>
      <span className="prime-metric-label">{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}