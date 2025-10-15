import Image from "next/image";

export default function DetailedInfoCard({ vehicle }) {
  if (!vehicle) {
    return (
      <div className="h-full bg-white overflow-y-auto">
        <div className="= rounded-sm p-6 text-center text-gray-500">
          Select a vehicle from the list to see its details.
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white overflow-y-auto rounded-lg shadow min-h-0 min-w-0 ">
      <div className="=  p-6">
        {/* Vehicle Details */}
        <div className="mb-4">
          <h3 className="text-xl font-bold text-black mb-4 border-b border-gray-300 pb-1">
            Vehicle Details
          </h3>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Time</span>
              {/*Use 'timestamp' and format it */}
              <span className="text-md text-black">
                {new Date(vehicle.timestamp).toLocaleString()}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Type</span>
              {/*Use 'location' from backend data */}
              <span className="text-md text-black capitalize">
                {vehicle.vehicle_type || "N/A"}
              </span>
            </div>

            {vehicle.color != "Unknown" && (
              <div className="flex justify-between">
                <span className="text-md font-semibold text-black">Colour</span>
                <span className="text-md text-black capitalize">
                  {vehicle.color}
                </span>
              </div>
            )}

            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Camera</span>
              {/*Use 'location' from backend data */}
              <span className="text-md text-black">
                {vehicle.location || "N/A"}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Junction</span>
              <span className="text-md text-black">ELATHUR_JN</span>
            </div>

            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Project</span>
              <span className="text-md text-black">KOZHIKODE</span>
            </div>

            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">GPS</span>
              <span className="text-md text-black">11.352214, 75.740565</span>
            </div>

            {/* <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">Violation ID</span>
              <span className="text-[14px] text-black">P08C180-2025080815188</span>
            </div> */}
          </div>
        </div>

        {vehicle.plate_url &&
        vehicle.vehicle_number &&
        vehicle.vehicle_number !== "N/A" ? (
          <div className="mb-4 flex items-center">
            <Image
              src={vehicle.plate_url}
              alt="License Plate"
              width={240}
              height={80}
              className="rounded border border-gray-200"
            />
          </div>
        ) : null}

        {/* Vehicle Registration Number */}
        <div>
          <h3 className="text-[14px] font-bold text-black mb-4 border-b border-gray-300 pb-3">
            Vehicle Registration Number
          </h3>

          {/*Use 'vehicle_number' from backend data */}
          <span className="text-[16px] text-black">
            {vehicle.vehicle_number || "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
}
