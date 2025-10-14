import Image from "next/image";

export default function DetailedInfoCard({ vehicle }) {
  if (!vehicle) {
    return (
      <div className="h-full bg-white overflow-y-auto">
        <div className="border border-gray-300 rounded-sm p-6 text-center text-gray-500">
          Select a vehicle from the list to see its details.
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white overflow-y-auto">
      <div className="border border-gray-300 rounded-sm p-6">
        {/* Transaction Details */}
        <div className="mb-6">
          <h3 className="text-[15px] font-bold text-black mb-4 border-b border-gray-300 pb-3">
            Transaction Details
          </h3>

          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">Time</span>
              {/* MODIFIED: Use 'timestamp' and format it */}
              <span className="text-[14px] text-black">
                {new Date(vehicle.timestamp).toLocaleString()}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">
                Camera
              </span>
              {/* MODIFIED: Use 'location' from backend data */}
              <span className="text-[14px] text-black">
                {vehicle.location || "N/A"}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">
                Junction
              </span>
              <span className="text-[14px] text-black">ELATHUR_JN</span>
            </div>

            <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">
                Project
              </span>
              <span className="text-[14px] text-black">KOZHIKODE</span>
            </div>

            <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">GPS</span>
              <span className="text-[14px] text-black">
                11.352214, 75.740565
              </span>
            </div>

            {/* <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">Violation ID</span>
              <span className="text-[14px] text-black">P08C180-2025080815188</span>
            </div> */}

            <div className="flex justify-between">
              <span className="text-[14px] font-semibold text-black">
                Status
              </span>
              {/* MODIFIED: Use 'status' from backend data */}
              <span className="text-[14px] text-black capitalize">
                {vehicle.status || "New"}
              </span>
            </div>
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

          {/* MODIFIED: Use 'vehicle_number' from backend data */}
          <span className="text-[16px] text-black">
            {vehicle.vehicle_number || "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
}
