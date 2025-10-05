"use client"

import { useState } from "react";
import Image from "next/image";
import VehicleCard from "@/components/VehicleCard";
import DetailedInfo from "@/components/DetailedInfo";
import vehicleData from "@/data/vehicleData.json";


export default function Home() {
  const [selectedVehicle, setSelectedVehicle] = useState(vehicleData.vehicles[0]);

  return (
    <div className="bg-grey-50 min-h-screen px-auto md:px-12 flex md:flex-row flex-col pt-4 pb-4 gap-4"> 

      {/* vehicle views */}
      <div className="flex bg-white p-4 md:flex-3 flex-col min-w-0">

        <div className="h-[200px] md:flex-1 p-4 mb-4 md:min-h-0 flex items-center justify-center relative"> 
          {selectedVehicle?.vehicleImage ? (
            <Image 
              src={selectedVehicle.vehicleImage}
              alt={`Vehicle ${selectedVehicle.licensePlate}`}
              fill
              className="rounded"
            />
          ) : (
            <div className="text-gray-500">No vehicle image available</div>
          )}
        </div>
        
        {/* Vehicle pass-by details */}
        <div className="h-[220px] md:flex-2 pt-4 pr-2 overflow-y-auto space-y-2 md:min-h-0">
          {vehicleData.vehicles.map((vehicle) => (
            <VehicleCard 
              key={vehicle.sNo} 
              vehicle={vehicle}
              isSelected={selectedVehicle?.sNo === vehicle.sNo}
              onSelect={() => setSelectedVehicle(vehicle)}
            />
          ))}
        </div>

      </div> 

      {/* Detailed information */}
      <div className="w-full md:w-[30%] md:h-screen overflow-y-auto p-4 md:p-2 relative overflow-hidden">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <Image 
            src="/hexagonal-bg.jpg" 
            alt="Background" 
            fill
            className="object-cover"
          />
        </div>
        
        {/* Content Container */}
        <div className="relative z-10">
          <DetailedInfo vehicle={selectedVehicle} />
        </div>
      </div>

    </div>
  );
}
