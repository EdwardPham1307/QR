import React, { useState } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [originalUrl, setOriginalUrl] = useState("");
  const [shortenedData, setShortenedData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const shortenUrl = async () => {
    if (!originalUrl.trim()) {
      setError("Vui lòng nhập URL");
      return;
    }

    setLoading(true);
    setError("");
    setShortenedData(null);

    try {
      const response = await axios.post(`${API}/shorten`, {
        original_url: originalUrl
      });
      
      setShortenedData(response.data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Có lỗi xảy ra khi rút gọn URL");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert("Đã sao chép vào clipboard!");
    });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      shortenUrl();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-800 mb-4">
            🔗 LinkShort
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Rút gọn URL dễ dàng, nhanh chóng và miễn phí. Tạo liên kết ngắn gọn cho việc chia sẻ tiện lợi.
          </p>
        </div>

        {/* Main Card */}
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            {/* URL Input Section */}
            <div className="mb-8">
              <label className="block text-lg font-semibold text-gray-700 mb-3">
                Nhập URL cần rút gọn:
              </label>
              <div className="flex flex-col md:flex-row gap-4">
                <input
                  type="url"
                  value={originalUrl}
                  onChange={(e) => setOriginalUrl(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="https://example.com/very-long-url..."
                  className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-lg"
                  disabled={loading}
                />
                <button
                  onClick={shortenUrl}
                  disabled={loading}
                  className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? "Đang xử lý..." : "Rút gọn"}
                </button>
              </div>
              {error && (
                <p className="text-red-500 mt-2 text-sm">{error}</p>
              )}
            </div>

            {/* Result Section */}
            {shortenedData && (
              <div className="border-t pt-8">
                <h3 className="text-2xl font-semibold text-gray-800 mb-6">
                  ✅ URL đã được rút gọn thành công!
                </h3>
                
                <div className="space-y-6">
                  {/* Original URL */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <label className="block text-sm font-medium text-gray-600 mb-2">
                      URL gốc:
                    </label>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-800 break-all flex-1 mr-4">
                        {shortenedData.original_url}
                      </span>
                    </div>
                  </div>

                  {/* Shortened URL */}
                  <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
                    <label className="block text-sm font-medium text-blue-700 mb-2">
                      URL rút gọn:
                    </label>
                    <div className="flex items-center justify-between">
                      <span className="text-blue-800 font-semibold text-lg flex-1 mr-4">
                        {shortenedData.short_url}
                      </span>
                      <button
                        onClick={() => copyToClipboard(shortenedData.short_url)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                      >
                        📋 Sao chép
                      </button>
                    </div>
                  </div>

                  {/* Short Code Info */}
                  <div className="bg-green-50 rounded-lg p-4">
                    <label className="block text-sm font-medium text-green-700 mb-2">
                      Mã rút gọn:
                    </label>
                    <span className="text-green-800 font-mono text-lg">
                      {shortenedData.short_code}
                    </span>
                    <p className="text-green-600 text-sm mt-2">
                      Sử dụng mã này để xem thống kê tại trang báo cáo
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Features Section */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-md p-6 text-center">
              <div className="text-3xl mb-4">⚡</div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Nhanh chóng</h3>
              <p className="text-gray-600">Rút gọn URL trong tích tắc</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6 text-center">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Thống kê</h3>
              <p className="text-gray-600">Theo dõi lượt click và phân tích</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6 text-center">
              <div className="text-3xl mb-4">🔒</div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Bảo mật</h3>
              <p className="text-gray-600">An toàn và đáng tin cậy</p>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center text-gray-500">
            <p>© 2025 LinkShort - Dịch vụ rút gọn URL hàng đầu</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;