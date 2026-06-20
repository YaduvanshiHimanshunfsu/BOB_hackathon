import React, { useState } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
    const [userId, setUserId] = useState('');
    const [password, setPassword] = useState('');
    const [sessionId] = useState(() => `sess_${Math.random().toString(36).substring(2, 10)}`);
    const navigate = useNavigate();

    const { triggerEvent } = useTelemetry(userId || 'anonymous', sessionId);

    const handleLogin = async (e) => {
        e.preventDefault();
        await triggerEvent('login');
        localStorage.setItem('currentUser', userId);
        localStorage.setItem('currentSession', sessionId);
        navigate('/dashboard');
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 relative overflow-hidden">
            {/* Animated Background Blobs */}
            <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-red-800 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
            <div className="absolute top-[20%] right-[-10%] w-96 h-96 bg-rose-800 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
            <div className="absolute bottom-[-20%] left-[20%] w-96 h-96 bg-orange-800 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>

            <div className="z-10 bg-white/10 backdrop-blur-xl border border-white/20 p-10 rounded-2xl shadow-2xl w-full max-w-md">
                <div className="text-center mb-10">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-tr from-orange-500 to-red-500 mb-4 shadow-lg">
                        <span className="text-white font-bold text-2xl">B</span>
                    </div>
                    <h1 className="text-3xl font-extrabold text-red-500 tracking-tight">ATTACKER TERMINAL</h1>
                    <p className="text-rose-200 mt-2 text-sm font-medium">Cloned Bank of Baroda Portal</p>
                </div>
                
                <form onSubmit={handleLogin} className="space-y-6">
                    <div>
                        <label className="block text-sm font-semibold text-slate-300 mb-2">Customer ID</label>
                        <input 
                            type="text" 
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all"
                            placeholder="Enter any username to test"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-slate-300 mb-2">Password</label>
                        <input 
                            type="password" 
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button 
                        type="submit" 
                        className="w-full bg-gradient-to-r from-red-800 to-red-600 hover:from-red-700 hover:to-red-500 text-white font-bold py-3 px-4 rounded-xl shadow-lg transform transition hover:-translate-y-0.5"
                    >
                        Execute Credential Stuffing
                    </button>
                    
                    <p className="text-center text-xs text-slate-400 mt-6">
                        Interact with the form to train the Behavioral AI!
                    </p>
                </form>
            </div>
        </div>
    );
}
