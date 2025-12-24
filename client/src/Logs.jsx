import React, { useEffect, useState, useMemo } from "react";
import Header from "./Header";

function Logs() {
    const [logs, setLogs] = useState([]);
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("all");
    const [sort, setSort] = useState("newest");
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [total, setTotal] = useState(0);
    const [selectedRow, setSelectedRow] = useState(null);

    const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);

    useEffect(() => {
        loadLogs();
    }, [search, status, sort, page, pageSize]);

    const loadLogs = async () => {
        try {
            const params = new URLSearchParams({
                page,
                page_size: pageSize,
                sort,
            });
            if (search) params.append("search", search);
            if (status !== "all") params.append("status", status);

            const res = await fetch(`http://localhost:5000/api/logs?${params.toString()}`);
            const data = await res.json();
            setLogs(data.items);
            setTotal(data.total);
        } catch (e) {
            console.error("שגיאה בטעינת לוגים", e);
        }
    };

    const handleClear = async () => {
        if (!window.confirm("האם אתה בטוח שברצונך למחוק את כל הלוגים?")) return;
        try {
            await fetch("http://localhost:5000/api/logs?confirm=YES", { method: "DELETE" });
            setPage(1);
            await loadLogs();
        } catch (e) {
            alert("שגיאה במחיקת הלוגים");
        }
    };

    return (
        <>
            <Header />
            <div className="min-h-screen bg-gradient-to-tr from-gray-900 via-sky-800 to-indigo-900 text-white px-6 py-12">
                <div className="max-w-4xl mx-auto bg-white/10 backdrop-blur-md border border-white/20 rounded-3xl shadow-2xl p-8">
                    <h1 className="text-3xl font-extrabold text-center text-white mb-6 drop-shadow">📋 לוגים של פעילות הסינון</h1>

                    <div className="flex flex-wrap gap-3 mb-6 items-center justify-between">
                        <input
                            className="border border-white/30 bg-gray-800 rounded-xl px-4 py-2 text-white placeholder-gray-400 w-64"
                            placeholder="חיפוש לפי כתובת או תוצאה"
                            value={search}
                            onChange={(e) => { setPage(1); setSearch(e.target.value); }}
                        />
                        <select
                            className="rounded-xl bg-gray-800 border border-white/30 px-4 py-2 text-white"
                            value={status}
                            onChange={(e) => { setPage(1); setStatus(e.target.value); }}
                        >
                            <option value="all">הכל</option>
                            <option value="blocked">חסומים</option>
                            <option value="allowed">מאושרים</option>
                        </select>
                        <select
                            className="rounded-xl bg-gray-800 border border-white/30 px-4 py-2 text-white"
                            value={sort}
                            onChange={(e) => setSort(e.target.value)}
                        >
                            <option value="newest">מהחדש לישן</option>
                            <option value="oldest">מהישן לחדש</option>
                        </select>
                        <button
                            onClick={handleClear}
                            className="bg-red-500 hover:bg-red-600 text-white font-bold px-4 py-2 rounded-xl"
                        >
                            🧹 נקה לוגים
                        </button>
                        <button
                            onClick={async () => {
                                try {
                                    const response = await fetch("http://localhost:5000/api/logs/export");
                                    const blob = await response.blob();
                                    const url = window.URL.createObjectURL(blob);

                                    const a = document.createElement("a");
                                    a.href = url;
                                    a.download = "logs.xlsx";
                                    document.body.appendChild(a);
                                    a.click();
                                    a.remove();
                                    window.URL.revokeObjectURL(url);
                                } catch (err) {
                                    console.error("שגיאה בייצוא:", err);
                                    alert("אירעה שגיאה בעת הורדת הקובץ");
                                }
                            }}
                            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                        >
                            📥 ייצא לאקסל
                        </button>
                    </div>

                    {logs.length === 0 ? (
                        <p className="text-center text-gray-300">אין לוגים להצגה עדיין.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left rtl:text-right text-white">
                                <thead className="text-xs uppercase bg-white/10 text-gray-100">
                                <tr>
                                    <th className="px-4 py-3">⏱ תאריך ושעה</th>
                                    <th className="px-4 py-3">🌐 כתובת URL</th>
                                    <th className="px-4 py-3">📌 תוצאה</th>
                                </tr>
                                </thead>
                                <tbody>
                                {logs.map((log, index) => (
                                    <tr
                                        key={index}
                                        onClick={() => setSelectedRow(index)}
                                        className={`border-b border-white/10 transition cursor-pointer ${
                                            selectedRow === index ? "bg-gray-700" : "hover:bg-gray-800"
                                        }`}
                                    >
                                        <td className="px-4 py-3 font-mono">{log.timestamp}</td>
                                        <td className="px-4 py-3">{log.url}</td>
                                        <td className={`px-4 py-3 font-semibold ${log.result === "blocked" ? "text-red-400" : "text-green-400"}`}>
                                            {log.result === "blocked" ? "❌ חסום" : "✅ מותר"}
                                        </td>
                                    </tr>
                                ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    <div className="flex justify-between items-center mt-6 text-sm text-white">
                        <span>סה"כ {total} רשומות</span>
                        <div className="flex gap-2 items-center">
                            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="rounded border border-white/20 px-3 py-1 disabled:opacity-40">הקודם</button>
                            <span>עמוד {page} מתוך {totalPages}</span>
                            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="rounded border border-white/20 px-3 py-1 disabled:opacity-40">הבא</button>
                            <select value={pageSize} onChange={e => { setPage(1); setPageSize(parseInt(e.target.value)) }} className="rounded border border-white/20 bg-gray-800 px-2 py-1 text-white">
                                {[10, 25, 50, 100].map(size => <option key={size} value={size}>{size} בעמוד</option>)}
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}

export default Logs;
