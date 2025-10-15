"use client";

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/Layout/Sidebar";
import DashboardView from "@/components/Views/DashboardView";
import Loader from "@/components/Loader/Loader";

export default function Home() {
  // View state
  const [activeView, setActiveView] = useState("dashboard");

  // WebSocket & Vehicle state
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [showLoader, setShowLoader] = useState(true);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const updateTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  // Reconnection configuration
  const INITIAL_RECONNECT_DELAY = 2000;
  const MAX_RECONNECT_DELAY = 4000;
  const MAX_RECONNECT_ATTEMPTS = Infinity;

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        const newVehicle = JSON.parse(event.data);

        if (updateTimeoutRef.current) {
          clearTimeout(updateTimeoutRef.current);
        }

        updateTimeoutRef.current = setTimeout(() => {
          setVehicles((prevVehicles) => [newVehicle, ...prevVehicles]);
          setSelectedVehicle(newVehicle);
        }, 500);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.onclose = () => {
        console.log("WebSocket closed");
        setIsConnected(false);
        setShowLoader(true);
        wsRef.current = null;
        scheduleReconnect();
      };
    } catch (error) {
      console.error("WebSocket connection failed:", error);
      setIsConnected(false);
      setShowLoader(true);
      wsRef.current = null;
      scheduleReconnect();
    }
  };

  const scheduleReconnect = () => {
    if (reconnectTimeoutRef.current) {
      return;
    }

    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      console.error("Max reconnection attempts reached");
      return;
    }

    const exponentialDelay = Math.min(
      INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttemptsRef.current),
      MAX_RECONNECT_DELAY
    );

    const jitter = Math.random() * 1000;
    const delay = exponentialDelay + jitter;

    console.log(
      `Reconnecting in ${Math.round(delay / 1000)}s (attempt ${
        reconnectAttemptsRef.current + 1
      })`
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectTimeoutRef.current = null;
      reconnectAttemptsRef.current++;
      connectWebSocket();
    }, delay);
  };

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleLoaderComplete = () => {
    setShowLoader(false);
  };

  // Render active view
  const renderView = () => {
    switch (activeView) {
      case "dashboard":
        return (
          <DashboardView
            vehicles={vehicles}
            selectedVehicle={selectedVehicle}
            setSelectedVehicle={setSelectedVehicle}
            isConnected={isConnected}
          />
        );
      case "live":
        return <div className="p-8">Live Stream View (Coming Soon)</div>;
      case "search":
        return <div className="p-8">Search View (Coming Soon)</div>;
      default:
        return null;
    }
  };

  return (
    <>
      <div className="flex h-screen">
        {/* Sidebar - Fixed Left */}
        <Sidebar activeView={activeView} setActiveView={setActiveView} />

        {/* Main Content Area - Right Side */}
        <main className="flex-1 ml-[200px] overflow-auto">{renderView()}</main>
      </div>

      {/* Loader overlay - shows on top when needed */}
      {showLoader && (
        <Loader
          isConnected={isConnected}
          onAnimationComplete={handleLoaderComplete}
        />
      )}
    </>
  );
}
