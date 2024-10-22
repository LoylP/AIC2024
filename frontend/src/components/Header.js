"use client";
import React from "react";
import logo from "../static/logo.png";

const Header = ({ children }) => {
  return (
    <div className="bg-slate-900 flex py-5">
      <div className="mx-auto w-full">
        <h1 className="text-white text-center text-[100%] font-bold flex items-center justify-center">
          Images Search App
          <div className="h-[3%] w-[3%] pointer-events-none animate-spin duration-[1s] linear">
            <img src={logo} className="h-full" alt="logo" />
          </div>
        </h1>
        {children}
      </div>
    </div>
  );
};

export default Header;
