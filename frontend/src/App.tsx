import React from 'react';
import { Link, Routes, Route } from 'react-router-dom';
import { ArrowLeft, FileQuestion } from 'lucide-react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { LandingPage } from './pages/LandingPage';
import { WorkspacePage } from './pages/WorkspacePage';
import { AnalysisDetailPage } from './pages/AnalysisDetailPage';
import { HistoryPage } from './pages/HistoryPage';
import { ModelsPage } from './pages/ModelsPage';
import { ExtensionGuidePage } from './pages/ExtensionGuidePage';

export const App: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/workspace" element={<WorkspacePage />} />
          <Route path="/analysis/:id" element={<AnalysisDetailPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/extension-guide" element={<ExtensionGuidePage />} />
          <Route path="*" element={<div className="page-wrap flex min-h-[55vh] flex-col items-center justify-center py-20 text-center"><span className="grid h-14 w-14 place-items-center rounded-2xl bg-clay-50 text-clay-700"><FileQuestion className="h-7 w-7" /></span><h1 className="mt-5 text-2xl font-bold text-ink-900">We couldn’t find that page</h1><p className="mt-2 text-sm text-stone-600">The address may be incomplete or the page may have moved.</p><Link to="/" className="btn-secondary mt-6"><ArrowLeft className="h-4 w-4" />Back to overview</Link></div>} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
};
