import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-4">
      <h1 className="text-6xl font-extrabold text-emerald-400 mb-4">404</h1>
      <p className="text-xl text-slate-300 mb-6">Page Not Found</p>
      <Link
        to="/"
        className="px-6 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-medium transition-colors"
      >
        Return Home
      </Link>
    </div>
  );
};
