import axios from 'axios';

const API_URL = "https://4xvvcrodcr3numaj6iwec625my0ouptf.lambda-url.us-east-2.on.aws";

export const analyzeFolder = async (files, batchId) => {
  const fileArray = Array.from(files);
  const results = [];
  const CONCURRENCY_LIMIT = 5; // Process 5 images at a time

  // Process in chunks to avoid 429 errors
  for (let i = 0; i < fileArray.length; i += CONCURRENCY_LIMIT) {
    const chunk = fileArray.slice(i, i + CONCURRENCY_LIMIT);
    
    const chunkPromises = chunk.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('batch_id', String(batchId));

      try {
        const response = await axios.post(`${API_URL}/analyze`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        return { ...response.data, fileName: file.name };
      } catch (err) {
        console.error(`Error analyzing ${file.name}:`, err);
        return { fileName: file.name, count: 0, error: true };
      }
    });

    // Wait for the current group of 5 to finish before starting the next group
    const chunkResults = await Promise.all(chunkPromises);
    results.push(...chunkResults);
  }

  return results;
};