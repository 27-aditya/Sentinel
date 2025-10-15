"use client";

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/Layout/Sidebar";
import DashboardView from "@/components/Views/DashboardView";
import LiveStreamView from "@/components/Views/LiveStreamView";
import Loader from "@/components/Loader/Loader";

const MAX_VEHICLES = 100;

export default function Home() {
  const [activeView, setActiveView] = useState("dashboard");
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [showLoader, setShowLoader] = useState(true);
  const [isInitialDataLoaded, setIsInitialDataLoaded] = useState(false);
  const [formattedDate, setFormattedDate] = useState("");
  const [formattedTime, setFormattedTime] = useState("");

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const updateTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);

  // Date Time Logic
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      setFormattedDate(
        now.toLocaleDateString("en-IN", {
          weekday: "long",
          year: "numeric",
          month: "long",
          day: "numeric",
        })
      );
      setFormattedTime(
        now.toLocaleTimeString("en-IN", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        })
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Fetch initial data from API
  const fetchInitialVehicles = async () => {
    try {
      // Add ?limit=500 query parameter
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/vehicles?limit=${MAX_VEHICLES}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch vehicles");
      }

      const data = await response.json();

      setVehicles(data);

      // Set the first vehicle as selected if available
      if (data.length > 0) {
        setSelectedVehicle(data[0]);
      }

      setIsInitialDataLoaded(true);
      console.log(`✓ Loaded ${data.length} vehicles from database`);
    } catch (error) {
      console.error("Error fetching initial vehicles:", error);
      setIsInitialDataLoaded(true);
    }
  };

  // WebSocket Logic
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
          setVehicles((prevVehicles) => {
            // Add new vehicle at the start
            const updatedVehicles = [newVehicle, ...prevVehicles];

            // Keep only the most recent MAX_VEHICLES (remove oldest)
            if (updatedVehicles.length > MAX_VEHICLES) {
              return updatedVehicles.slice(0, MAX_VEHICLES);
            }

            return updatedVehicles;
          });

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
    fetchInitialVehicles();
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
    const commonProps = { formattedDate, formattedTime };
    switch (activeView) {
      case "dashboard":
        return (
          <DashboardView
            {...commonProps}
            vehicles={vehicles}
            selectedVehicle={selectedVehicle}
            setSelectedVehicle={setSelectedVehicle}
            isConnected={isConnected}
            isInitialDataLoaded={isInitialDataLoaded}
          />
        );
      case "live":
        return <LiveStreamView {...commonProps} />;
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
