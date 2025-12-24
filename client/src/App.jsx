import React, { useState, useEffect } from "react";
import Header from "./Header";
import logo from "./logo.jpg";
import { Link } from "react-router-dom";

function App() {
    const [filterEnabled, setFilterEnabled] = useState(null);

    useEffect(() => {
        fetch("http://localhost:5000/api/status")
            .then(res => res.json())
            .then(data => setFilterEnabled(data.filter_enabled));
    }, []);

    const toggleFilter = () => {
        fetch("http://localhost:5000/api/toggle", { method: "POST" })
            .then(res => res.json())
            .then(data => setFilterEnabled(data.filter_enabled));
    };

    return (
        <>
            <Header />
            <div className="min-h-screen bg-gradient-to-tr from-gray-900 via-sky-800 to-indigo-900 flex flex-col items-center justify-center px-4 py-12">
                <div className="bg-white/10 backdrop-blur-md border border-white/20 shadow-xl rounded-3xl p-10 max-w-2xl w-full text-center">
                    <img src={logo} alt="SafeNet Logo" className="w-24 h-24 mx-auto mb-6 rounded-full shadow-lg border-4 border-white/30" />
                    <h1 className="text-4xl font-extrabold text-white drop-shadow mb-2">SafeNet</h1>
                    <p className="text-lg text-sky-100 mb-6">מערכת סינון רשת חכמה</p>

                    <div className="text-sm text-red-300">
                        🚫היום נחסמו 17 נסיונות גישה
                    </div>

                    <div className="mb-6">
                        <p className={`text-xl font-semibold ${filterEnabled === null ? "text-gray-300" : filterEnabled ? "text-green-400" : "text-red-400"}`}>
                            {filterEnabled === null ? "טוען..." : filterEnabled ? "מצב סינון: פעיל" : "מצב סינון: כבוי"}
                        </p>
                        <button
                            onClick={toggleFilter}
                            className={`mt-4 px-6 py-3 rounded-xl text-white text-lg transition-all duration-300 transform hover:scale-105 shadow-md ${
                                filterEnabled ? "bg-gradient-to-r from-red-500 to-red-700" : "bg-gradient-to-r from-green-500 to-green-700"
                            }`}
                        >
                            {filterEnabled ? "כבה סינון" : "הפעל סינון"}
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-white" dir="rtl">
                        <div className="bg-white/10 p-4 rounded-xl border border-white/20 shadow">
                            <h2 className="text-xl font-semibold mb-2">⛔ חסימה חכמה</h2>
                            <p>
                                סינון אתרים בעייתיים לפי <span dir="ltr" className="font-mono">blacklist</span> מותאם אישית.
                            </p>
                        </div>

                        <div className="bg-white/10 p-4 rounded-xl border border-white/20 shadow">
                            <h2 className="text-xl font-semibold mb-2">🧠 רמות סינון</h2>
                            <p>בחירה בין רמות סינון – בסיסי, רגיל, קפדני.</p>
                        </div>

                        <div className="bg-white/10 p-4 rounded-xl border border-white/20 shadow">
                            <h2 className="text-xl font-semibold mb-2">📜 לוגים ודו"חות</h2>
                            <p>
                                מעקב מלא אחרי ניסיונות גישה – כולל <span dir="ltr" className="font-mono">Excel</span> לייצוא.
                            </p>
                        </div>
                    </div>


                    <div className="mt-6">
                        <Link to="/logs" className="text-blue-300 hover:underline text-sm">
                            📋 לצפייה בלוגים
                        </Link>

                    </div>
                </div>
            </div>
        </>
    );
}

export default App;