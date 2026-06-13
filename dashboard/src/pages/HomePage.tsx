import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Upload,
  Brain,
  Users,
  BarChart3,
  MessageSquareText,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

const features = [
  {
    icon: Upload,
    title: 'Attendance Upload',
    description: 'Drop Excel/CSV files — column headers auto-normalize. No manual mapping needed.',
  },
  {
    icon: Brain,
    title: 'AI Risk Scoring',
    description: 'LLM-powered risk assessment (0–100) with factor analysis and recommendations.',
  },
  {
    icon: Users,
    title: 'Employee Directory',
    description: 'Profiles created automatically on upload. One-click risk analysis per employee.',
  },
  {
    icon: BarChart3,
    title: 'Real-time Dashboard',
    description: 'Live stats — present, late, missing punches. Strike distribution tracking.',
  },
  {
    icon: MessageSquareText,
    title: 'RAG Copilot',
    description: 'Chat with HR policies. FAISS vector search + LLM for accurate answers.',
  },
  {
    icon: ShieldCheck,
    title: 'Behavior Analysis',
    description: '90-day lookback detects trends, anomalies, and potential causes.',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
  },
};

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-full space-y-0">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-[-200px] right-[-200px] w-[500px] h-[500px] rounded-full bg-primary/5 blur-3xl" />
          <div className="absolute bottom-[-200px] left-[-200px] w-[400px] h-[400px] rounded-full bg-primary/5 blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto pt-16 pb-12 px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: 'easeOut' }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              Workforce Intelligence Platform
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-foreground leading-tight mb-4">
              AI-Powered
              <br />
              <span className="text-primary">Attendance Management</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed">
              Upload attendance logs, get instant AI risk scores, behavior analysis,
              and real-time dashboards — all powered by LLMs and vector search.
            </p>
            <div className="flex items-center justify-center gap-4">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate('/dashboard')}
                className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all inline-flex items-center gap-2"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate('/attendance')}
                className="px-6 py-3 bg-card border border-border text-foreground rounded-xl font-medium hover:bg-accent transition-all inline-flex items-center gap-2"
              >
                Upload Attendance
              </motion.button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Quick stats */}
      <section className="max-w-4xl mx-auto px-6 pb-12">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="grid grid-cols-3 gap-4"
        >
          {[
            { label: 'Upload & Go', desc: 'Auto-normalize columns' },
            { label: 'AI Risk Scores', desc: '0–100 with reasoning' },
            { label: '90-Day Analysis', desc: 'Trends & anomalies' },
          ].map((stat) => (
            <motion.div
              key={stat.label}
              variants={itemVariants}
              className="bg-card border border-border rounded-xl p-5 text-center"
            >
              <p className="text-sm font-semibold text-foreground">{stat.label}</p>
              <p className="text-xs text-muted-foreground mt-1">{stat.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10"
        >
          <h2 className="text-2xl md:text-3xl font-bold text-foreground">
            Everything you need to manage attendance
          </h2>
          <p className="text-muted-foreground mt-2">
            No manual setup. Upload data and get instant insights.
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                variants={itemVariants}
                whileHover={{ y: -4 }}
                className="bg-card border border-border rounded-xl p-5 group cursor-default transition-shadow hover:shadow-lg hover:shadow-primary/5"
              >
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary/20 transition-colors">
                  <Icon className="w-5 h-5 text-primary" />
                </div>
                <h3 className="text-sm font-semibold text-foreground mb-1.5">
                  {feature.title}
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </motion.div>
      </section>

      {/* How it works */}
      <section className="max-w-4xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="text-center mb-10"
        >
          <h2 className="text-2xl md:text-3xl font-bold text-foreground">
            How it works
          </h2>
          <p className="text-muted-foreground mt-2">
            Three steps to get started
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-50px' }}
          className="grid md:grid-cols-3 gap-6"
        >
          {[
            {
              step: '01',
              title: 'Upload Data',
              desc: 'Drop your Excel or CSV attendance file. Column headers auto-normalize.',
              icon: Upload,
            },
            {
              step: '02',
              title: 'AI Analysis',
              desc: 'Risk scores, behavior analysis, and anomaly detection run automatically.',
              icon: Brain,
            },
            {
              step: '03',
              title: 'Take Action',
              desc: 'View dashboards, manage employees, and chat with HR policies via Copilot.',
              icon: CheckCircle2,
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.step}
                variants={itemVariants}
                className="bg-card border border-border rounded-xl p-6 text-center relative"
              >
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <span className="text-xs font-bold text-primary uppercase tracking-wider">
                  Step {item.step}
                </span>
                <h3 className="text-sm font-semibold text-foreground mt-1 mb-2">{item.title}</h3>
                <p className="text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
              </motion.div>
            );
          })}
        </motion.div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="bg-card border border-border rounded-2xl p-8 md:p-10 text-center"
        >
          <h2 className="text-xl md:text-2xl font-bold text-foreground mb-3">
            Ready to get started?
          </h2>
          <p className="text-sm text-muted-foreground mb-6 max-w-lg mx-auto">
            Upload your first attendance file and see AI-powered insights in seconds.
          </p>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/attendance')}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all inline-flex items-center gap-2"
          >
            Upload Your First File
            <Upload className="w-4 h-4" />
          </motion.button>
        </motion.div>
      </section>
    </div>
  );
}
