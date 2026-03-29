import React, { useEffect, useState } from 'react';
import { Calendar, Hash, Image as ImageIcon, ChevronRight, Folder } from 'lucide-react';
import axios from 'axios';

const API_URL = "https://4xvvcrodcr3numaj6iwec625my0ouptf.lambda-url.us-east-2.on.aws";

const History = () => {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get(`${API_URL}/batches`);
        setBatches(response.data);
      } catch (err) {
        console.error("Failed to load history", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) return <div className="text-center py-20 text-slate-400">Loading Batch History...</div>;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-2">
        <Folder className="text-orange-500" /> Processed Batches
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {batches.map((batch) => (
          <div key={batch.batchId} className="bg-slate-800 border border-slate-700 rounded-2xl overflow-hidden hover:border-orange-500/50 transition-all group cursor-pointer">
            {/* Thumbnail Preview */}
            <div className="h-40 bg-slate-900 relative">
              <img 
                src={batch.thumbnail} 
                className="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity"
                alt="Batch Preview"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent" />
              <div className="absolute bottom-4 left-4">
                <span className="bg-orange-600 text-white text-xs font-bold px-2 py-1 rounded">
                  {batch.totalYield} Oranges Found
                </span>
              </div>
            </div>

            {/* Batch Details */}
            <div className="p-5">
              <h3 className="text-white font-semibold mb-3 truncate">{batch.batchId}</h3>
              
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Calendar size={14} />
                  {new Date(batch.createdAt).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <ImageIcon size={14} />
                  {batch.fileCount} Images Processed
                </div>
              </div>

              <button className="mt-4 w-full py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors">
                View Batch Details <ChevronRight size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default History;