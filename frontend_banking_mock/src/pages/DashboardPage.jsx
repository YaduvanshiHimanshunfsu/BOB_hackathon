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

        // Poll API for real-time risk score every 5 seconds (for UI feedback)
        const interval = setInterval(async () => {
            try {
                const apiHost = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                const res = await axios.get(`${apiHost}/api/v1/risk/${userId}`);
                setRiskState(res.data);
                
                // If critical, force logout
                if (res.data.action === "DENY") {
                    alert("CRITICAL RISK DETECTED. Session terminated.");
                    handleLogout();
                }
            } catch (err) {
                console.log("Waiting for risk data...");
            }
        }, 5000);

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

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-brand-blue text-white p-4 flex justify-between items-center shadow-md">
                <h1 className="text-xl font-bold">BOB Dashboard</h1>
                <div className="flex items-center space-x-4">
                    <span>Welcome, {userId}</span>
                    <button onClick={handleLogout} className="bg-white text-brand-blue px-3 py-1 rounded text-sm hover:bg-gray-200">
                        Logout
                    </button>
                </div>
            </header>

            <div className="max-w-7xl mx-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* Main Action Area */}
                <div className="md:col-span-2 space-y-6">
                    <div className="bg-white p-6 rounded-lg shadow">
                        <h2 className="text-lg font-semibold mb-4 border-b pb-2">Fund Transfer</h2>
                        <form onSubmit={handleTransfer} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Beneficiary Account</label>
                                <input 
                                    type="text" 
                                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                                    value={beneficiary}
                                    onChange={(e) => setBeneficiary(e.target.value)}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Amount (₹)</label>
                                <input 
                                    type="number" 
                                    className="mt-1 block w-full border border-gray-300 rounded-md p-2"
                                    value={amount}
                                    onChange={(e) => setAmount(e.target.value)}
                                    required
                                />
                            </div>
                            <button type="submit" className="bg-brand-orange text-white px-4 py-2 rounded-md hover:bg-orange-600 transition">
                                Transfer Funds
                            </button>
                        </form>
                    </div>
                </div>

                {/* Risk Indicator Panel */}
                <div className="bg-white p-6 rounded-lg shadow border-l-4 border-gray-200">
                    <h2 className="text-lg font-semibold mb-4 text-gray-700">Live Security Status</h2>
                    {riskState ? (
                        <div className="space-y-4">
                            <div>
                                <p className="text-sm text-gray-500">Risk Tier</p>
                                <p className={`text-xl font-bold ${
                                    riskState.risk_tier === 'LOW' ? 'text-green-600' :
                                    riskState.risk_tier === 'MODERATE' ? 'text-yellow-500' :
                                    riskState.risk_tier === 'HIGH' ? 'text-orange-500' : 'text-red-600'
                                }`}>
                                    {riskState.risk_tier}
                                </p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Composite Score</p>
                                <p className="text-2xl font-mono">{riskState.composite_risk_score.toFixed(1)} / 100</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Policy Action</p>
                                <span className="inline-block bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-medium">
                                    {riskState.action}
                                </span>
                            </div>
                            <hr />
                            <div className="text-xs text-gray-400">
                                <p>Behavioral Score: {riskState.behavioral_score.toFixed(1)}</p>
                                <p>Device Score: {riskState.device_score.toFixed(1)}</p>
                            </div>
                        </div>
                    ) : (
                        <p className="text-sm text-gray-500 animate-pulse">Computing baseline...</p>
                    )}
                </div>

            </div>
        </div>
    );
}
