"use client";

import { useState, useEffect, useRef } from "react";
import Sidebar from "@/components/Layout/Sidebar";
import DashboardView from "@/components/Views/DashboardView";
import LiveStreamView from "@/components/Views/LiveStreamView";
import SearchView from "@/components/Views/SearchView";
import Loader from "@/components/Loader/Loader";
import {
  apiFetch,
  clearAccessToken,
  getAccessToken,
  login,
  websocketUrl,
} from "@/lib/api";

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
  const [autoSelectEnabled, setAutoSelectEnabled] = useState(true); // NEW: Track auto-select state
  const [accessToken, setAccessToken] = useState(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const updateTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const autoSelectEnabledRef = useRef(true);

  // Sync ref with state
  useEffect(() => {
    autoSelectEnabledRef.current = autoSelectEnabled;
  }, [autoSelectEnabled]);

  useEffect(() => {
    setAccessToken(getAccessToken());
    setAuthChecked(true);
  }, []);

  const handleLogin = async (event) => {
    event.preventDefault();
    setIsLoggingIn(true);
    setAuthError("");
    try {
      const token = await login(username, password);
      setAccessToken(token);
    } catch (error) {
      setAuthError(error.message || "Login failed");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    clearAccessToken();
    setAccessToken(null);
    setVehicles([]);
    setSelectedVehicle(null);
  };

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
      const response = await apiFetch(`/api/vehicles?limit=${MAX_VEHICLES}`);

      if (!response.ok) {
        throw new Error("Failed to fetch vehicles");
      }

      const data = await response.json();

      setVehicles(data);

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
      const ws = new WebSocket(websocketUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("✓ WebSocket connected");
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        const newVehicle = JSON.parse(event.data);

        if (updateTimeoutRef.current) {
          clearTimeout(updateTimeoutRef.current);
        }

        // Capture auto-select state IMMEDIATELY (before setTimeout)
        const shouldAutoSelect = autoSelectEnabledRef.current;

        updateTimeoutRef.current = setTimeout(() => {
          setVehicles((prevVehicles) => {
            const updatedVehicles = [newVehicle, ...prevVehicles];

            if (updatedVehicles.length > MAX_VEHICLES) {
              return updatedVehicles.slice(0, MAX_VEHICLES);
            }

            return updatedVehicles;
          });

          // Use captured value
          if (shouldAutoSelect) {
            setSelectedVehicle(newVehicle);
            console.log("✓ Auto-selected new vehicle:", newVehicle.vehicle_id);
          } else {
            console.log("✗ Auto-select disabled, keeping current selection");
          }
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
    if (!accessToken) return;
    setIsInitialDataLoaded(false);
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
  }, [accessToken]);

  const handleLoaderComplete = () => {
    setShowLoader(false);
  };

  if (!authChecked) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-200">
        <p className="text-gray-600">Loading Sentinel...</p>
      </div>
    );
  }

  if (!accessToken) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-200">
        <form
          onSubmit={handleLogin}
          className="w-full max-w-sm bg-white rounded-lg shadow p-8 space-y-4"
        >
          <h1 className="text-2xl font-semibold text-gray-900">Sentinel Central</h1>
          <p className="text-sm text-gray-500">Sign in to view live vehicle detections.</p>
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Email"
            autoComplete="username"
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            autoComplete="current-password"
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
          {authError && <p className="text-sm text-red-600">{authError}</p>}
          <button
            type="submit"
            disabled={isLoggingIn}
            className="w-full px-4 py-2 rounded bg-gray-900 text-white hover:bg-gray-800 disabled:bg-gray-400"
          >
            {isLoggingIn ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    );
  }

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
            setVehicles={setVehicles}
            isConnected={isConnected}
            isInitialDataLoaded={isInitialDataLoaded}
            autoSelectEnabled={autoSelectEnabled}
            setAutoSelectEnabled={setAutoSelectEnabled}
          />
        );
      case "live":
        return <LiveStreamView {...commonProps} />;
      case "search":
        return <SearchView /> ; 
      default:
        return null;
    }
  };

  return (
    <>
      <div className="flex h-screen">
        <Sidebar activeView={activeView} setActiveView={setActiveView} />
        <main className="flex-1 ml-[200px] overflow-auto">{renderView()}</main>
        <button
          onClick={handleLogout}
          className="fixed bottom-4 right-4 z-50 px-3 py-1.5 rounded bg-gray-900 text-white text-sm shadow hover:bg-gray-800"
        >
          Log out
        </button>
      </div>

      {showLoader && (
        <Loader
          isConnected={isConnected}
          onAnimationComplete={handleLoaderComplete}
        />
      )}
    </>
  );
}
