import Image from "next/image";

export default function VehicleCard({ vehicle, isSelected, onSelect }){ 
  return (

    <div 
      onClick={onSelect}
      className={`relative flex flex-wrap item-center justify-between md:gap-2 border p-4 cursor-pointer transition-all duration-300 ease-in-out ${
        isSelected 
          ? 'border-gray-500 bg-gray-100' 
          : 'border-gray-300 hover:border-gray-500'
      } bg-white`}
    >
      
        <div className="absolute top-4 left-4">
          <span className="text-[14px] font-bold text-black">#{vehicle.sNo}</span>
        </div>

        <div className="flex flex-col items-start justify-center w-24 p-2 md:ml-6 ml-6 gap-1">
          <div className="text-[14px] font-semibold text-black text-left">License Plate</div>
          {vehicle.licensePlateImage ? (
            <Image 
              src={vehicle.licensePlateImage} 
              alt={`License plate ${vehicle.licensePlate}`}
              width={80}
              height={30}
            />
          ) : (
            <div className="text-[14px] text-black text-left">{vehicle.licensePlate}</div>
          )}
        </div>

        <div className="flex flex-col items-start justify-center w-24 p-2 gap-1">
          <div className="text-[14px] font-semibold text-black text-left">Registration No</div>
          <div className="text-[14px] text-black text-left">{vehicle.regNumber}</div>
        </div>
        
        <div className="flex flex-col items-start justify-center w-24 p-2 gap-1">
          <span className="font-semibold text-[14px] text-black text-left">Colour</span>
          <span className="text-[14px] text-black text-left">{vehicle.color}</span>
        </div>
        
        <div className="flex flex-col items-start justify-center w-24 p-2 gap-1">
          <span className="font-semibold text-[14px] text-black text-left">Timestamp</span>
          <span className="text-[14px] text-black text-left">{vehicle.timeStamp}</span>
        </div>

        <div className="flex flex-col items-start justify-center w-24 p-2 gap-1">
          <span className="font-semibold text-[14px] text-black text-left">Camera Location</span>
          <span className="text-[14px] text-black break-words text-left">{vehicle.cameraLocation}</span>
        </div>
        

        {/* Commented out feaures well add later */}

        {/* <div className="flex flex-col w-24 p-2">
          <span className="font-semibold text-xs text-gray-700">Violation Type</span>
          <span className="text-xs text-gray-900 mt-1">{vehicle.violationType}</span>
        </div> */}

        {/* <div className="flex flex-col w-24 p-2">
          <span className="font-semibold text-xs text-gray-700">Violation Description</span>
          <span className="text-xs text-gray-900 break-words">{vehicle.violationDescription}</span>
        </div> */}

        {/* <div className="flex flex-col w-24 p-2">
          <span className="font-semibold text-xs text-gray-700">Category</span>
          <span className="text-xs text-gray-900 mt-1">{vehicle.category}</span>
        </div> */}

        {/* <div className="flex flex-col w-24 p-2">
          <span className="font-semibold text-xs text-gray-700">Status</span>
          <span className="text-xs text-gray-900 mt-1">{vehicle.status}</span>
        </div> */}

        {/* <div className="flex flex-col w-24 p-2">
          <span className="font-semibold text-xs text-gray-700">Make</span>
          <span className="text-xs text-gray-900">{vehicle.make}</span>
        </div> */}

        {/* <div className="flex flex-col w-24 p-2">
          <span className="font-semibold text-xs text-gray-700">Logo</span>
          {vehicle.logoImage ? (
            <Image 
              src={vehicle.logoImage} 
              alt={`${vehicle.make} logo`}
              width={32}
              height={32}
              className="rounded mt-1 border border-gray-300"
            />
          ) : (
            <div className="w-8 h-8 border border-gray-400 rounded flex items-center justify-center text-xs mt-1 text-gray-600">
              {vehicle.make ? vehicle.make.charAt(0) : '?'}
            </div>
          )}
        </div> */}

        {/* <div className="flex flex-col w-24 p-2">
          <span className="font-semibold text-xs text-gray-700">Vehicle Type</span>
          <span className="text-xs text-gray-900">{vehicle.vehicleType}</span>
        </div> */}

    </div>
  );
}
