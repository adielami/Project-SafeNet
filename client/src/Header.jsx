import React from "react";
import { Link, useLocation } from "react-router-dom";
import logo from "./logo.jpg";

function Header() {
    const location = useLocation();
    const isActive = (path) => location.pathname === path;

    return (
        <header className="bg-gray-950 shadow-md sticky top-0 z-50 border-b border-white/10">
            <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
                {/* לוגו ושם */}
                <Link to="/" className="flex items-center space-x-3 rtl:space-x-reverse">
                    <img src={logo} alt="SafeNet Logo" className="w-10 h-10 rounded-full border-2 border-white/20 shadow-sm" />
                    <span className="text-xl sm:text-2xl font-bold text-white drop-shadow">SafeNet</span>
                </Link>

                {/* ניווט */}
                <nav className="space-x-6 rtl:space-x-reverse text-sm sm:text-base">
                    <Link
                        to="/"
                        className={isActive("/") ? "text-blue-400 font-semibold" : "text-white/70 hover:text-blue-300 transition"}
                    >
                        Home page 🏠
                    </Link>
                    <Link
                        to="/logs"
                        className={isActive("logs") ? "text-blue-400 font-semibold" : "text-white/70 hover:text-blue-300 transition"}
                    >
                        Logs 📋
                    </Link>
                    <Link
                        to="/settings"
                        className={isActive("/settings") ? "text-blue-400 font-semibold" : "text-white/70 hover:text-blue-300 transition"}
                    >
                        Settings ⚙️
                    </Link>

                </nav>
            </div>
        </header>
    );
}

export default Header;