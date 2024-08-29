"use client";
import React from "react";
import logo from "../logo.svg";

const Header = ({ children }) => {
  return (
    <div className="bg-slate-900 flex items-center py-10">
      <div className="mx-auto w-full">
        <h1 className="text-white text-center text-3xl font-bold mb-5 flex items-center justify-center">
          Images Search App
          <div className="h-[5%] w-[5%] pointer-events-none animate-spin duration-[10s] linear">
            <img src={logo} className="h-full" alt="logo" />
          </div>
        </h1>
        {children}
      </div>
    </div>
  );
};

export default Header;
