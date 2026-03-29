import React, { useState } from 'react';
import { FolderUp, LayoutGrid, List, Activity, Loader2, Leaf, History as HistoryIcon } from 'lucide-react';
import { analyzeFolder } from './services/api';
import History from './components/History'; // Assuming your History component is here

function App() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState('grid');
  const [activeTab, setActiveTab] = useState('upload');


const handleFolderUpload = async (e) => {
  const files = e.target.files;
  if (!files || files.length === 0) return;

  // 1. Create the ID immediately
  const folderName = files[0].webkitRelativePath.split('/')[0] || "Orchard";
  const timestamp = Date.now();
  const generatedBatchId = `${folderName}_${timestamp}`;

  setLoading(true);
  setResults([]);
  
  try {
    // 2. PASS the generated ID to the service
    const batchResults = await analyzeFolder(files, generatedBatchId);
    setResults(batchResults);
  } catch (err) {
    console.error("Batch failed", err);
  } finally {
    setLoading(false);
  }
};

  const totalYield = results.reduce((sum, res) => sum + (res.count || 0), 0);

  return (
    <div className="min-h-screen bg-[#0f1115] text-slate-200 p-6">
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-orange-500 p-2 rounded-lg">
            <Leaf className="text-white w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Yield Estimate <span className="text-orange-500">Pro</span></h1>
        </div>

        {results.length > 0 && activeTab === 'upload' && (
          <div className="flex gap-6 bg-slate-800/50 p-4 rounded-xl border border-slate-700">
            <div className="text-center">
              <p className="text-xs text-slate-400 uppercase font-bold">Total Estimated Yield</p>
              <p className="text-xl font-bold text-orange-500">{totalYield} Oranges</p>
            </div>
            <div className="border-r border-slate-700"></div>
            <div className="text-center">
              <p className="text-xs text-slate-400 uppercase font-bold">Files Processed</p>
              <p className="text-xl font-bold text-white">{results.length}</p>
            </div>
          </div>
        )}
      </header>

      {/* Tab Navigation */}
      <div className="max-w-7xl mx-auto mb-8 flex border-b border-slate-800">
        <button 
          onClick={() => setActiveTab('upload')} 
          className={`px-6 py-3 font-semibold transition-all ${activeTab === 'upload' ? 'text-orange-500 border-b-2 border-orange-500' : 'text-slate-400'}`}
        >
          Upload & Analyze
        </button>
        <button 
          onClick={() => setActiveTab('history')} 
          className={`px-6 py-3 font-semibold transition-all ${activeTab === 'history' ? 'text-orange-500 border-b-2 border-orange-500' : 'text-slate-400'}`}
        >
          Yield History
        </button>
      </div>

      <main className="max-w-7xl mx-auto">
        {activeTab === 'history' ? (
          <History />
        ) : (
          <>
            {/* Upload Action Bar */}
            <div className="flex justify-between items-center mb-6">
              <label className="bg-orange-600 hover:bg-orange-500 text-white px-6 py-3 rounded-lg font-semibold flex items-center gap-2 cursor-pointer transition-all">
                <FolderUp className="w-5 h-5" />
                Upload Orchard Folder
                <input 
                  type="file" 
                  className="hidden" 
                  webkitdirectory="true" 
                  directory="true" 
                  onChange={handleFolderUpload} 
                />
              </label>

              <div className="flex bg-slate-800 rounded-lg p-1">
                <button onClick={() => setViewMode('grid')} className={`p-2 rounded ${viewMode === 'grid' ? 'bg-slate-600 text-white' : 'text-slate-400'}`}><LayoutGrid className="w-4 h-4" /></button>
                <button onClick={() => setViewMode('list')} className={`p-2 rounded ${viewMode === 'list' ? 'bg-slate-600 text-white' : 'text-slate-400'}`}><List className="w-4 h-4" /></button>
              </div>
            </div>

            {/* Results Area */}
            {loading ? (
              <div className="flex flex-col items-center justify-center py-20">
                <Loader2 className="w-12 h-12 text-orange-500 animate-spin mb-4" />
                <p className="text-slate-400 animate-pulse">Processing...</p>
              </div>
            ) : results.length > 0 ? (
              <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6' : 'space-y-4'}>
                {results.map((res, idx) => (
                  <div key={idx} className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden group">
                    <div className="aspect-video relative">
                      <img src={res.result_url} alt={res.fileName} className="w-full h-full object-cover" />
                      <div className="absolute top-2 right-2 bg-black/60 px-2 py-1 rounded text-xs font-bold text-orange-400">
                        {res.count} Oranges
                      </div>
                    </div>
                    <div className="p-3 flex justify-between items-center">
                      <span className="text-xs text-slate-400 truncate w-32">{res.fileName}</span>
                      <Activity className="w-4 h-4 text-green-500" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="border-2 border-dashed border-slate-800 rounded-2xl py-20 text-center">
                <p className="text-slate-600">No data analyzed yet. Select a folder to begin.</p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;