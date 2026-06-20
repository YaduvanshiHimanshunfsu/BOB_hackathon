import React, { useEffect, useState } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function DashboardPage() {
    const userId = localStorage.getItem('currentUser');
    const sessionId = localStorage.getItem('currentSession');
    const navigate = useNavigate();
    const { triggerEvent } = useTelemetry(userId, sessionId);

    const [amount, setAmount] = useState('');
    const [beneficiary, setBeneficiary] = useState('');
    const [riskState, setRiskState] = useState(null);

    useEffect(() => {
        if (!userId) {
            navigate('/');
            return;
        }

        const interval = setInterval(async () => {
            try {
                const apiHost = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const res = await axios.get(`${apiHost}/api/v1/risk/${userId}`);
                setRiskState(res.data);
                
                if (res.data.action === "DENY") {
                    alert("CRITICAL RISK DETECTED. Session terminated.");
                    handleLogout();
                }
            } catch (err) {
                console.log("Waiting for risk data...");
            }
        }, 3000); // Polling faster for demo

        return () => clearInterval(interval);
    }, [userId, navigate]);

    const handleTransfer = async (e) => {
        e.preventDefault();
        await triggerEvent('fund_transfer_initiate');
        
        if (riskState?.action === "CHALLENGE_HARD") {
            alert("HIGH RISK: Step-up authentication required (OTP sent).");
        } else if (riskState?.action === "CHALLENGE_SOFT") {
            alert("MODERATE RISK: Please answer your security question.");
        } else {
            alert(`Transfer of ₹${amount} to ${beneficiary} successful!`);
        }
    };

    const handleLogout = async () => {
        await triggerEvent('logout');
        localStorage.clear();
        navigate('/');
    };

    if (!userId) return null;

    // Helper for tier colors
    const getTierColor = (tier) => {
        switch(tier) {
            case 'LOW': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
            case 'MODERATE': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
            case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
            case 'CRITICAL': return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
            default: return 'text-slate-400 bg-slate-800 border-slate-700';
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            {/* Navbar */}
            <nav className="bg-slate-900 border-b border-red-900/50 px-6 py-4 flex justify-between items-center sticky top-0 z-50">
                <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded bg-gradient-to-tr from-rose-700 to-red-900 flex items-center justify-center font-bold text-white shadow-lg shadow-red-500/20">A</div>
                    <h1 className="text-xl font-bold tracking-tight text-white">ATTACKER <span className="font-light text-red-400">Terminal</span></h1>
                </div>
                <div className="flex items-center space-x-6">
                    <span className="text-sm text-rose-400 flex items-center"><div className="w-2 h-2 rounded-full bg-red-500 mr-2 animate-pulse"></div> Root access: {userId}</span>
                    <button onClick={handleLogout} className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm transition font-medium border border-slate-700">
                        Disconnect
                    </button>
                </div>
            </nav>

            <div className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-8 mt-6">
                
                {/* Main Action Area */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-slate-900/50 backdrop-blur-sm p-8 rounded-2xl border border-red-900/50 shadow-xl">
                        <h2 className="text-2xl font-bold mb-6 text-white flex items-center">
                            <span className="bg-red-500/20 text-red-400 p-2 rounded-lg mr-3">💰</span> 
                            Siphon Funds
                        </h2>
                        <form onSubmit={handleTransfer} className="space-y-5">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-2">Drop Account</label>
                                <input 
                                    type="text" 
                                    className="w-full bg-slate-950 border border-red-900/50 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
                                    placeholder="Enter drop account number"
                                    value={beneficiary}
                                    onChange={(e) => setBeneficiary(e.target.value)}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-2">Amount (₹)</label>
                                <input 
                                    type="number" 
                                    className="w-full bg-slate-950 border border-red-900/50 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
                                    placeholder="0.00"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    required
                                />
                            </div>
                            <button type="submit" className="w-full bg-red-700 hover:bg-red-600 text-white font-bold py-4 px-4 rounded-xl shadow-lg shadow-red-500/25 transition">
                                Execute Unauthorized Transfer
                            </button>
                        </form>
                    </div>

                    {/* Educational Banner */}
                    <div className="bg-red-900/20 border border-red-500/30 rounded-2xl p-6 flex items-start space-x-4">
                        <div className="text-red-400 text-2xl">⚠️</div>
                        <div>
                            <h3 className="text-white font-bold mb-1">Evasion Status: Compromised</h3>
                            <p className="text-slate-400 text-sm leading-relaxed">
                                This terminal runs on a different physical device footprint than the victim. The CIFE ML Engine should instantly detect the hardware mismatch and block this attempt, regardless of whether you know the password.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Risk Indicator Panel */}
                <div className="bg-slate-900/80 backdrop-blur-md p-8 rounded-2xl border border-slate-700 shadow-2xl relative overflow-hidden">
                    {/* Background glow effect based on risk */}
                    <div className={`absolute -inset-1 blur-3xl opacity-20 z-0 ${
                        !riskState ? 'bg-red-500' :
                        riskState.risk_tier === 'LOW' ? 'bg-emerald-500' :
                        riskState.risk_tier === 'MODERATE' ? 'bg-amber-500' :
                        riskState.risk_tier === 'HIGH' ? 'bg-orange-500' : 'bg-rose-500'
                    }`}></div>

                    <div className="relative z-10">
                        <h2 className="text-lg font-bold mb-6 text-white flex justify-between items-center tracking-wide">
                            DEFENSE DETECTION
                            <span className="flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-red-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                            </span>
                        </h2>
                        
                        {riskState ? (
                            <div className="space-y-6">
                                {/* Big Score Display */}
                                <div className="text-center p-6 bg-slate-950/50 rounded-2xl border border-slate-800">
                                    <p className="text-sm font-medium text-slate-500 mb-2 uppercase tracking-wider">Victim's Engine Score</p>
                                    <div className="flex items-baseline justify-center">
                                        <span className="text-5xl font-black text-white">{riskState.composite_risk_score.toFixed(1)}</span>
                                        <span className="text-xl text-slate-500 ml-1">/100</span>
                                    </div>
                                    <div className={`mt-4 inline-block px-4 py-1.5 rounded-full text-xs font-bold border uppercase tracking-widest ${getTierColor(riskState.risk_tier)}`}>
                                        {riskState.risk_tier} RISK
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <div className="flex justify-between items-center p-3 bg-slate-800/30 rounded-lg">
                                        <span className="text-slate-400 text-sm">Policy Action</span>
                                        <span className="text-white font-mono text-sm font-bold bg-slate-700 px-2 py-1 rounded">{riskState.action}</span>
                                    </div>
                                    <div className="flex justify-between items-center p-3 bg-slate-800/30 rounded-lg">
                                        <span className="text-slate-400 text-sm">Behavioral Trust</span>
                                        <span className="text-white font-mono text-sm">{riskState.behavioral_score.toFixed(1)} pts</span>
                                    </div>
                                    <div className="flex justify-between items-center p-3 bg-slate-800/30 rounded-lg">
                                        <span className="text-slate-400 text-sm">Device Fingerprint</span>
                                        <span className="text-white font-mono text-sm">{riskState.device_score.toFixed(1)} pts</span>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-64 space-y-4">
                                <div className="w-10 h-10 border-4 border-red-500/20 border-t-red-500 rounded-full animate-spin"></div>
                                <p className="text-sm text-red-400 font-medium animate-pulse">Probing defenses...</p>
                            </div>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
