// src/App.tsx
import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/HomePage";
import Favourites from "./pages/FavouritesPage";
import Layout from "./components/Layout";

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/favourites" element={<Favourites />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
};

export default App;
