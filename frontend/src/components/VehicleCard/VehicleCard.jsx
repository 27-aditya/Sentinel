import Image from "next/image";
import { AlertTriangle } from "lucide-react";

export default function VehicleCard({ vehicle, isSelected, onSelect }) {
  const indianPlateRegex =
    /^(?:[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}|[0-9]{2}BH\d{4}[A-Z]{2})$/i;

  const formatPlate = (plate) => {
    if (!plate) return "N/A";
    const clean = plate.toUpperCase().replace(/\s+/g, "");

    // Standard Indian format: e.g., KL60L4436 or TN28NH8708
    const normalMatch = clean.match(/^([A-Z]{2})(\d{1,2})([A-Z]{1,2})(\d{4})$/);
    if (normalMatch) {
      const [, state, rto, series, number] = normalMatch;
      return `${state} ${rto} ${series} ${number}`;
    }

    // Bharat series format: e.g., 23BH1234AA
    const bhMatch = clean.match(/^(\d{2})BH(\d{4})([A-Z]{2})$/);
    if (bhMatch) {
      const [, year, num, suffix] = bhMatch;
      return `${year} BH ${num} ${suffix}`;
    }

    // Otherwise, invalid plate — return as-is
    return plate;
  };

  const formatLocation = (loc) => {
    if (!loc) return "N/A";
    return loc
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  };

  const plateNumber = vehicle.vehicle_number || "";
  const isValidPlate = indianPlateRegex.test(plateNumber);
  const formattedPlate = formatPlate(plateNumber);
  const formattedLocation = formatLocation(vehicle.location);

  return (
    <div
      onClick={onSelect}
      className={`border cursor-pointer transition-all duration-300 ease-in-out rounded-lg shadow `}
    >
      {/* Table Header - Only show once for all cards */}
      <div className="grid grid-cols-6 gap-4 border-b border-gray-200 bg-gray-200 px-4 py-2 rounded-t-lg">
        <div className="text-sm font-semibold text-gray-700">Plate Image</div>
        <div className="text-sm font-semibold text-gray-700">Plate Number</div>
        <div className="text-sm font-semibold text-gray-700">Vehicle Type</div>
        <div className="text-sm font-semibold text-gray-700">Colour</div>
        <div className="text-sm font-semibold text-gray-700">Timestamp</div>
        <div className="text-sm font-semibold text-gray-700">Location</div>
      </div>

      {/* Table Data */}
      <div className="grid grid-cols-6 gap-4 px-4 py-3 items-center">
        {/* Plate Image */}
        <div className="flex items-center justify-start">
          {vehicle.plate_url &&
          vehicle.vehicle_number &&
          vehicle.vehicle_number !== "N/A" ? (
            <Image
              src={vehicle.plate_url}
              alt="License Plate"
              width={100}
              height={35}
              className="rounded"
            />
          ) : (
            <span className="text-sm text-gray-400">N/A</span>
          )}
        </div>

        {/* Registration Number */}
        <div className="relative flex items-center gap-2 text-sm text-gray-900">
          {formattedPlate}
          {!isValidPlate && (
            <AlertTriangle
              size={16}
              className="text-yellow-500"
              title="Invalid plate format"
            />
          )}
        </div>

        {/* Vehicle Type */}
        <div className="text-sm text-gray-900 capitalize">
          {vehicle.vehicle_type || "N/A"}
        </div>

        {/* Colour */}
        <div className="flex items-center gap-2">
          <div
            className="w-6 h-6 rounded-full border border-gray-300"
            style={{ backgroundColor: vehicle.color_hex || "#000" }}
          ></div>
          <span className="text-sm text-gray-900 capitalize">
            {vehicle.color || "N/A"}
          </span>
        </div>

        {/* Timestamp */}
        <div className="text-sm text-gray-900">
          {new Date(vehicle.timestamp).toLocaleString("en-IN", {
            dateStyle: "short",
            timeStyle: "short",
          })}
        </div>

        {/* Camera Location */}
        <div className="text-sm text-gray-900 break-words">
          {formattedLocation}
        </div>
      </div>
    </div>
  );
}
