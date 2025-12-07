'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, TrendingUp, TrendingDown, Minus, Activity, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { chatService } from '@/services/chatService';

export default function PredictionSection() {
    const [formData, setFormData] = useState({
        disease: '',
        criteria_text: '',
        phase: 2,
        target_enrollment: 100,
        site_count: 5,
        recruitment_duration: 12
    });

    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: name === 'disease' || name === 'criteria_text' ? value : parseInt(value) || 0
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setPrediction(null);

        try {
            const result = await chatService.predictEnrollment(formData);

            if (result.error) {
                setError(result.error);
            } else {
                setPrediction(result);
            }
        } catch (err) {
            setError(err.message || 'Failed to get prediction');
        } finally {
            setLoading(false);
        }
    };

    const getOutcomeColor = (outcome) => {
        switch (outcome) {
            case 'success': return 'text-green-500';
            case 'delayed': return 'text-yellow-500';
            case 'fail': return 'text-red-500';
            default: return 'text-gray-500';
        }
    };

    const getOutcomeIcon = (outcome) => {
        switch (outcome) {
            case 'success': return <TrendingUp className="w-8 h-8" />;
            case 'delayed': return <Minus className="w-8 h-8" />;
            case 'fail': return <TrendingDown className="w-8 h-8" />;
            default: return <Activity className="w-8 h-8" />;
        }
    };

    return (
        <section id="prediction" className="relative py-32 px-4 overflow-hidden">
            {/* Background gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#00ADB5]/5 to-transparent" />

            <div className="relative z-10 max-w-6xl mx-auto">
                {/* Section Header */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-16"
                >
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#00ADB5]/10 border border-[#00ADB5]/20 mb-6">
                        <Brain className="w-5 h-5 text-[#00ADB5]" />
                        <span className="text-sm font-medium text-[#00ADB5]">AI-Powered Predictions</span>
                    </div>

                    <h2 className="text-4xl md:text-5xl font-bold mb-4">
                        Check Enrollment <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#00ADB5] to-[#00C6FF]">Prediction</span>
                    </h2>

                    <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto">
                        Use our advanced ML model to predict clinical trial enrollment outcomes based on trial parameters
                    </p>
                </motion.div>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* Input Form */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                    >
                        <Card className="p-8 bg-[var(--card-bg)] backdrop-blur-lg border-[var(--border-color)]">
                            <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
                                <Activity className="w-6 h-6 text-[#00ADB5]" />
                                Trial Parameters
                            </h3>

                            <form onSubmit={handleSubmit} className="space-y-4">
                                {/* Disease Name */}
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Disease Name <span className="text-red-500">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        name="disease"
                                        value={formData.disease}
                                        onChange={handleInputChange}
                                        required
                                        placeholder="e.g., Type 2 Diabetes"
                                        className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] focus:border-[#00ADB5] focus:outline-none focus:ring-2 focus:ring-[#00ADB5]/20 transition-all"
                                    />
                                </div>

                                {/* Eligibility Criteria */}
                                <div>
                                    <label className="block text-sm font-medium mb-2">
                                        Eligibility Criteria (Optional)
                                    </label>
                                    <textarea
                                        name="criteria_text"
                                        value={formData.criteria_text}
                                        onChange={handleInputChange}
                                        placeholder="e.g., Adults aged 18-65 with HbA1c > 7.5%"
                                        rows={3}
                                        className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] focus:border-[#00ADB5] focus:outline-none focus:ring-2 focus:ring-[#00ADB5]/20 transition-all resize-none"
                                    />
                                </div>

                                {/* Trial Phase */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-2">Phase</label>
                                        <input
                                            type="number"
                                            name="phase"
                                            value={formData.phase}
                                            onChange={handleInputChange}
                                            min="0"
                                            max="4"
                                            className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] focus:border-[#00ADB5] focus:outline-none focus:ring-2 focus:ring-[#00ADB5]/20 transition-all"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium mb-2">Target Enrollment</label>
                                        <input
                                            type="number"
                                            name="target_enrollment"
                                            value={formData.target_enrollment}
                                            onChange={handleInputChange}
                                            min="1"
                                            className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] focus:border-[#00ADB5] focus:outline-none focus:ring-2 focus:ring-[#00ADB5]/20 transition-all"
                                        />
                                    </div>
                                </div>

                                {/* Site Count and Duration */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium mb-2">Number of Sites</label>
                                        <input
                                            type="number"
                                            name="site_count"
                                            value={formData.site_count}
                                            onChange={handleInputChange}
                                            min="1"
                                            className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] focus:border-[#00ADB5] focus:outline-none focus:ring-2 focus:ring-[#00ADB5]/20 transition-all"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium mb-2">Duration (months)</label>
                                        <input
                                            type="number"
                                            name="recruitment_duration"
                                            value={formData.recruitment_duration}
                                            onChange={handleInputChange}
                                            min="1"
                                            className="w-full px-4 py-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] focus:border-[#00ADB5] focus:outline-none focus:ring-2 focus:ring-[#00ADB5]/20 transition-all"
                                        />
                                    </div>
                                </div>

                                {/* Submit Button */}
                                <Button
                                    type="submit"
                                    disabled={loading || !formData.disease}
                                    className="w-full mt-6"
                                    size="lg"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                            Predicting...
                                        </>
                                    ) : (
                                        <>
                                            <Brain className="w-5 h-5 mr-2" />
                                            Get Prediction
                                        </>
                                    )}
                                </Button>
                            </form>
                        </Card>
                    </motion.div>

                    {/* Results Display */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                    >
                        <Card className="p-8 bg-[var(--card-bg)] backdrop-blur-lg border-[var(--border-color)] h-full">
                            <h3 className="text-2xl font-bold mb-6">Prediction Results</h3>

                            {!prediction && !error && !loading && (
                                <div className="flex flex-col items-center justify-center h-64 text-center text-[var(--text-tertiary)]">
                                    <Brain className="w-16 h-16 mb-4 opacity-30" />
                                    <p>Enter trial parameters and click "Get Prediction" to see results</p>
                                </div>
                            )}

                            {error && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="flex flex-col items-center justify-center h-64 text-center"
                                >
                                    <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6">
                                        <AlertCircle className="w-12 h-12 text-red-500 mb-3 mx-auto" />
                                        <p className="text-red-500 font-medium mb-2">Prediction Failed</p>
                                        <p className="text-sm text-[var(--text-secondary)]">{error}</p>
                                    </div>
                                </motion.div>
                            )}

                            {loading && (
                                <div className="flex flex-col items-center justify-center h-64">
                                    <Loader2 className="w-12 h-12 text-[#00ADB5] animate-spin mb-4" />
                                    <p className="text-[var(--text-secondary)]">Analyzing trial parameters...</p>
                                </div>
                            )}

                            {prediction && !error && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="space-y-6"
                                >
                                    {/* Predicted Outcome */}
                                    <div className="text-center pb-6 border-b border-[var(--border-color)]">
                                        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br ${getOutcomeColor(prediction.predicted_class)}/10 mb-4`}>
                                            <div className={getOutcomeColor(prediction.predicted_class)}>
                                                {getOutcomeIcon(prediction.predicted_class)}
                                            </div>
                                        </div>
                                        <h4 className="text-3xl font-bold capitalize mb-2">
                                            {prediction.predicted_class}
                                        </h4>
                                        <p className="text-[var(--text-secondary)]">
                                            Confidence: {(prediction.confidence_scores[prediction.predicted_class] * 100).toFixed(1)}%
                                        </p>
                                    </div>

                                    {/* Confidence Scores */}
                                    <div>
                                        <h5 className="font-semibold mb-3">Confidence Breakdown</h5>
                                        <div className="space-y-3">
                                            {Object.entries(prediction.confidence_scores).map(([outcome, score]) => (
                                                <div key={outcome}>
                                                    <div className="flex justify-between text-sm mb-1">
                                                        <span className="capitalize">{outcome}</span>
                                                        <span className="font-medium">{(score * 100).toFixed(1)}%</span>
                                                    </div>
                                                    <div className="h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${score * 100}%` }}
                                                            transition={{ duration: 0.6, delay: 0.2 }}
                                                            className={`h-full ${outcome === 'success' ? 'bg-green-500' :
                                                                    outcome === 'delayed' ? 'bg-yellow-500' :
                                                                        'bg-red-500'
                                                                }`}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Risk Drivers */}
                                    {prediction.top_risk_drivers && prediction.top_risk_drivers.length > 0 && (
                                        <div>
                                            <h5 className="font-semibold mb-3">Top Risk Drivers</h5>
                                            <div className="space-y-2">
                                                {prediction.top_risk_drivers.slice(0, 5).map((driver, idx) => (
                                                    <div
                                                        key={idx}
                                                        className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]"
                                                    >
                                                        <span className="capitalize text-sm">{driver.feature.replace('_', ' ')}</span>
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs text-[var(--text-tertiary)]">
                                                                {driver.value}
                                                            </span>
                                                            <div className={`px-2 py-1 rounded text-xs font-medium ${driver.direction === 'positive'
                                                                    ? 'bg-green-500/10 text-green-500'
                                                                    : 'bg-red-500/10 text-red-500'
                                                                }`}>
                                                                {driver.direction === 'positive' ? '↑' : '↓'}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </Card>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
