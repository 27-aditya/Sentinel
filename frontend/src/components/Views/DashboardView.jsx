// src/components/Views/DashboardView.jsx
"use client";

import Image from "next/image";
import { useRef, useEffect } from "react";
import VehicleCard from "@/components/VehicleCard/VehicleCard";
import DetailedInfo from "@/components/DetailedInfoCard/DetailedInfoCard";

export default function DashboardView({
  vehicles,
  selectedVehicle,
  setSelectedVehicle,
  setVehicles,
  isConnected,
  isInitialDataLoaded,
  formattedDate,
  formattedTime,
  autoSelectEnabled,
  setAutoSelectEnabled,
}) {
  const scrollContainerRef = useRef(null);

  // Handler to update vehicle in the list
  const handleVehicleUpdate = (updatedVehicle) => {
    setVehicles((prevVehicles) =>
      prevVehicles.map((v) =>
        v.vehicle_id === updatedVehicle.vehicle_id ? updatedVehicle : v
      )
    );

    if (selectedVehicle?.vehicle_id === updatedVehicle.vehicle_id) {
      setSelectedVehicle(updatedVehicle);
    }
  };

  // Handle plate edit start - disable auto-select if on latest vehicle
  const handlePlateEditStart = () => {
    // Only disable auto-select if currently viewing the latest vehicle
    if (
      vehicles.length > 0 &&
      selectedVehicle?.vehicle_id === vehicles[0].vehicle_id
    ) {
      setAutoSelectEnabled(false);
    }
  };

  // Handle vehicle selection
  const handleVehicleSelect = (vehicle) => {
    setSelectedVehicle(vehicle);

    // If clicking on the first vehicle, resume auto-select
    if (vehicles.length > 0 && vehicle.vehicle_id === vehicles[0].vehicle_id) {
      setAutoSelectEnabled(true);
    } else {
      // Otherwise, disable auto-select (manual selection)
      setAutoSelectEnabled(false);
    }
  };

  // Scroll to top and select newest vehicle
  const handleScrollToTop = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({ top: 0, behavior: "smooth" });
    }

    if (vehicles.length > 0) {
      setSelectedVehicle(vehicles[0]);
      setAutoSelectEnabled(true);
      console.log("✓ Scrolled to top & auto-select resumed");
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Dashboard Header */}
      <div className="bg-gray-200 px-6 pt-6 flex justify-between items-start">
        <h1 className="text-4xl font-semibold text-gray-900">Dashboard</h1>
        <div className="text-right">
          <div className="text-gray-700 text-md font-medium">
            {formattedDate}
          </div>
          <div className="text-gray-500 text-sm">{formattedTime}</div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="flex-1 bg-gray-200 px-auto md:px-6 flex md:flex-row flex-col p-6 pt-4 gap-4 min-h-0 overflow-auto">
        {/* Vehicle views */}
        <div className="flex flex-1 bg-white md:p-4 flex-col min-h-0 min-w-0 rounded-lg shadow relative">
          {/* Main Vehicle Image */}
          <div className="h-[400px] mb-4 md:min-h-0 flex items-center justify-center relative bg-black rounded">
            {selectedVehicle?.keyframe_url ? (
              <div className="relative w-full h-full rounded-lg overflow-hidden flex items-center justify-center bg-black">
                <Image
                  src={selectedVehicle.keyframe_url}
                  alt={`Vehicle ${selectedVehicle.vehicle_number}`}
                  fill
                  className="object-contain object-center transition-opacity duration-500 ease-in-out"
                  priority
                />
              </div>
            ) : (
              <div className="text-gray-500 flex flex-col items-center justify-center h-full space-y-2">
                {!isInitialDataLoaded ? (
                  <>
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gray-400"></div>
                    <p>Loading vehicle data...</p>
                  </>
                ) : (
                  <p>Waiting for vehicle detection...</p>
                )}
              </div>
            )}
          </div>

          {/* Vehicle pass-by list with scroll container */}
          <div
            ref={scrollContainerRef}
            className="h-[250px] pt-0 pr-2 overflow-y-auto space-y-2 min-h-0 relative"
          >
            {!isInitialDataLoaded ? (
              <div className="text-center text-gray-500 py-8">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-gray-400 mx-auto mb-2"></div>
                Loading vehicles...
              </div>
            ) : vehicles.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                No vehicles detected yet
              </div>
            ) : (
              vehicles.map((vehicle) => (
                <VehicleCard
                  key={vehicle.vehicle_id}
                  vehicle={vehicle}
                  isSelected={
                    selectedVehicle?.vehicle_id === vehicle.vehicle_id
                  }
                  onSelect={() => handleVehicleSelect(vehicle)}
                />
              ))
            )}
          </div>

          {/* Scroll to Top Button - Bottom Right */}
          {vehicles.length > 0 && (
            <button
              onClick={handleScrollToTop}
              className="absolute bottom-6 right-6 w-12 h-12 bg-gray-900 hover:bg-gray-800 text-white rounded-full shadow-lg transition-all duration-300 flex items-center justify-center z-10 hover:scale-110"
              title="Scroll to top & select newest"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 10l7-7m0 0l7 7m-7-7v18"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Detailed information panel */}
        <div className="w-full md:w-[30%] md:h-full overflow-y-auto">
          <DetailedInfo
            vehicle={selectedVehicle}
            onVehicleUpdate={handleVehicleUpdate}
            onPlateEditStart={handlePlateEditStart}
          />
        </div>
      </div>
    </div>
  );
}
