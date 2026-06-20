import React, { useState } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
    const [userId, setUserId] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    // Generate a quick random session ID for the demo
    const sessionId = `sess_${Math.random().toString(36).substring(2, 10)}`;

    // Initialize telemetry hook with dummy userId if not fully logged in yet,
    // but in a real app, you'd only track on login input focus or similar.
    // For the demo, we track the pre-login phase by pretending the username field is the ID.
    const { triggerEvent } = useTelemetry(userId || 'anonymous', sessionId);

    const handleLogin = async (e) => {
        e.preventDefault();
        
        // Trigger explicit login telemetry event
        await triggerEvent('login');

        // Simulate login success and save to local storage
        localStorage.setItem('currentUser', userId);
        localStorage.setItem('currentSession', sessionId);
        
        // Navigate to dashboard
        navigate('/dashboard');
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-8 rounded-lg shadow-md w-96">
                <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold text-brand-orange">Bank of Baroda</h1>
                    <p className="text-gray-500">Secure Digital Banking Mock</p>
                </div>
                
                <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Customer ID</label>
                        <input 
                            type="text" 
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                            value={userId}
                            onChange={(e) => setUserId(e.target.value)}
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Password</label>
                        <input 
                            type="password" 
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button 
                        type="submit" 
                        className="w-full bg-brand-blue text-white p-2 rounded-md hover:bg-blue-800 transition"
                    >
                        Login
                    </button>
                </form>
            </div>
        </div>
    );
}
