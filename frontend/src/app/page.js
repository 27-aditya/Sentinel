"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import VehicleCard from "@/components/VehicleCard";
import DetailedInfo from "@/components/DetailedInfo";
import vehicleData from "@/data/vehicleData.json";

export default function Home() {
  // State for the list of vehicles, initialized as an empty array\

  // const [vehicles, setVehicles] = useState([]);
  const [vehicles, setVehicles] = useState(() => vehicleData.vehicles || []);

  // State for the currently selected vehicle, initialized as null
  const [selectedVehicle, setSelectedVehicle] = useState(null);

  // useEffect hook to handle the WebSocket connection
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/updates");
    let updateTimeout;

    ws.onmessage = (event) => {
      const newVehicle = JSON.parse(event.data);
      
      // Clear any pending update
      if (updateTimeout) {
        clearTimeout(updateTimeout);
      }

      // Add a small delay for smoother updates (500ms)
      updateTimeout = setTimeout(() => {
        // Update the list of vehicles without a cap. The list will grow indefinitely.
        // Time complexity: O(N) where N is the number of existing vehicles.
        // Space complexity: O(N) as the array continues to grow.
        setVehicles(prevVehicles => [newVehicle, ...prevVehicles]);

        // Set the newly arrived vehicle as the currently selected one
        setSelectedVehicle(newVehicle);
      }, 500);
    };

    // Cleanup function to close the connection when the component unmounts
    return () => {
      if (updateTimeout) {
        clearTimeout(updateTimeout);
      }
      ws.close();
    };
  }, []); // The empty dependency array ensures this runs only once

  return (
    <div className="h-full bg-grey-100 px-auto md:px-12 flex md:flex-row flex-col p-6 gap-4 min-h-0"> 

      {/* vehicle views */}
      <div className="flex flex-1 bg-white md:p-4 flex-col min-h-0 min-w-0">

        <div className="h-[400px] p-4 mb-4 md:min-h-0 flex items-center justify-center relative"> 
          {/* MODIFIED: Use the live data from the backend */}
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
        <div className="flex-1 pt-4 pr-2 overflow-y-auto space-y-2 min-h-0">
          {/* MODIFIED: Map over the live 'vehicles' state instead of static data */}
          {vehicles.map((vehicle) => (
            <VehicleCard 
              key={vehicle.vehicle_id} // Use a unique ID from the data
              vehicle={vehicle}
              isSelected={selectedVehicle?.vehicle_id === vehicle.vehicle_id}
              onSelect={() => setSelectedVehicle(vehicle)}
            />
          ))}
        </div>

      </div> 

      {/* Detailed information */}
      <div className="w-full md:w-[30%] md:h-screen overflow-y-auto md:p-4 ">
        <DetailedInfo vehicle={selectedVehicle} />
      </div>

    </div>
  );
}

