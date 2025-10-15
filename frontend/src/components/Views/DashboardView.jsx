// src/components/Views/DashboardView.jsx
"use client";

import Image from "next/image";
import VehicleCard from "@/components/VehicleCard/VehicleCard";
import DetailedInfo from "@/components/DetailedInfoCard/DetailedInfoCard";

export default function DashboardView({
  vehicles,
  selectedVehicle,
  setSelectedVehicle,
  isConnected,
  formattedDate,
  formattedTime,
}) {
  return (
    <div className="h-full flex flex-col">
      {/* Dashboard Header */}
      <div className="bg-gray-100 px-6 pt-6 flex justify-between items-start">
        <h1 className="text-4xl font-semibold text-gray-900">Dashboard</h1>
        <div className="text-right">
          <div className="text-gray-700 text-md font-medium">
            {formattedDate}
          </div>
          <div className="text-gray-500 text-sm">{formattedTime}</div>
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="flex-1 bg-gray-100 px-auto md:px-12 flex md:flex-row flex-col p-6 pt-4 gap-4 min-h-0 overflow-auto">
        {/* Vehicle views */}
        <div className="flex flex-1 bg-white md:p-4 flex-col min-h-0 min-w-0 rounded-lg shadow">
          {/* Main Vehicle Image */}
          <div className="h-[400px] p-4 mb-4 md:min-h-0 flex items-center justify-center relative bg-gray-50 rounded">
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

          {/* Vehicle pass-by list */}
          <div className="h-[250px] pt-4 pr-2 overflow-y-auto space-y-2 min-h-0">
            {vehicles.length === 0 ? (
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
                  onSelect={() => setSelectedVehicle(vehicle)}
                />
              ))
            )}
          </div>
        </div>

        {/* Detailed information panel */}
        <div className="w-full md:w-[30%] md:h-full overflow-y-auto">
          <DetailedInfo vehicle={selectedVehicle} />
        </div>
      </div>
    </div>
  );
}
