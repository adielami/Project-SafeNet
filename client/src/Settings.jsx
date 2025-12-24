import React, { useEffect, useState } from "react";
import Header from "./Header";

function Settings() {
    const [filterLevel, setFilterLevel] = useState("normal");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch("http://localhost:5000/api/filter_level")
            .then((res) => res.json())
            .then((data) => {
                setFilterLevel(data.filter_level);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    const handleChange = (e) => {
        const level = e.target.value;
        setFilterLevel(level);
        fetch("http://localhost:5000/api/filter_level", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ level }),
        });
    };

    return (
        <>
            <Header />
            <div className="min-h-screen bg-gradient-to-tr from-gray-900 via-sky-800 to-indigo-900 px-6 py-12 text-white">
                <div className="max-w-3xl mx-auto bg-white/10 backdrop-blur-md border border-white/20 rounded-3xl shadow-xl p-10">
                    <h1 className="text-3xl font-bold text-center mb-6 drop-shadow">⚙️ הגדרות מערכת</h1>

                    <div className="mb-8">
                        <label htmlFor="filterLevel" className="block text-lg font-medium mb-2 text-white/80">
                            רמת סינון
                        </label>
                        <select
                            id="filterLevel"
                            value={filterLevel}
                            onChange={handleChange}
                            disabled={loading}
                            className="bg-gray-800 border border-white/30 text-white p-3 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-400"
                        >
                            <option value="normal" className="bg-gray-800 text-white">
                                רגיל – חסום אתרים בסיסיים בלבד
                            </option>
                            <option value="strict" className="bg-gray-800 text-white">
                                קפדני – חסום גם תוכן אפור
                            </option>
                        </select>
                    </div>

                    <div className="text-sm text-white/70 space-y-2">
                        <p>✅ ברמה <strong>רגילה</strong>, ייחסמו אתרים כמו רשתות חברתיות ואתרי תוכן פוגעניים</p>
                        <p>🔒ברמה <strong>קפדנית</strong>, ייחסמו גם אתרים עם תוכן חלקי או בעייתי</p>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Settings;