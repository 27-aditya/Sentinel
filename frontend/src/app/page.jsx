"use client";

import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import VehicleCard from "@/components/VehicleCard/VehicleCard";
import DetailedInfo from "@/components/DetailedInfoCard/DetailedInfoCard";
import Loader from "@/components/Loader/Loader";

export default function Home() {
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

  return (
    <>
      {/* Main content - always rendered */}
      <div className="h-full bg-grey-100 px-auto md:px-12 flex md:flex-row flex-col p-6 gap-4 min-h-0">
        {/* vehicle views */}
        <div className="flex flex-1 bg-white md:p-4 flex-col min-h-0 min-w-0">
          <div className="h-[400px] p-4 mb-4 md:min-h-0 flex items-center justify-center relative">
            {selectedVehicle?.keyframe_url ? (
              <Image
                src={selectedVehicle.keyframe_url}
                alt={`Vehicle ${selectedVehicle.vehicle_number}`}
                fill
                className="rounded object-cover transition-opacity duration-500 ease-in-out"
              />
            ) : (
              <div className="text-gray-500">Waiting for vehicle data...</div>
            )}
          </div>

          {/* Vehicle pass-by details */}
          <div className="h-[250px] pt-4 pr-2 overflow-y-auto space-y-2 min-h-0">
            {vehicles.map((vehicle) => (
              <VehicleCard
                key={vehicle.vehicle_id}
                vehicle={vehicle}
                isSelected={selectedVehicle?.vehicle_id === vehicle.vehicle_id}
                onSelect={() => setSelectedVehicle(vehicle)}
              />
            ))}
          </div>
        </div>

        {/* Detailed information */}
        <div className="w-full md:w-[30%] md:h-screen overflow-y-auto md:p-4">
          <DetailedInfo vehicle={selectedVehicle} />
        </div>
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
