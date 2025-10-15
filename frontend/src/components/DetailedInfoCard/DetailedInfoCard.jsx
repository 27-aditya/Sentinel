"use client";

import Image from "next/image";
import { useState, useEffect } from "react";

export default function DetailedInfoCard({ vehicle, onVehicleUpdate }) {
  const [editedPlateNumber, setEditedPlateNumber] = useState("");
  const [originalPlateNumber, setOriginalPlateNumber] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Indian License Plate Regex (e.g., KL11BM2325, DL01CA1234, MH12AB3456)
  const INDIAN_PLATE_REGEX = /^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$/;

  // Format location: CALICUT_JUNCTION -> Calicut Junction
  const formatLocation = (location) => {
    if (!location) return "N/A";
    return location
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");
  };

  // Update state when vehicle changes
  useEffect(() => {
    if (vehicle) {
      const plateNumber = vehicle.vehicle_number || "";
      setEditedPlateNumber(plateNumber);
      setOriginalPlateNumber(plateNumber);
      setUpdateError(null);
      setSuccessMessage(null);
    }
  }, [vehicle?.vehicle_id]);

  if (!vehicle) {
    return (
      <div className="h-full bg-white overflow-y-auto">
        <div className="rounded-sm p-6 text-center text-gray-500">
          Select a vehicle from the list to see its details.
        </div>
      </div>
    );
  }

  const hasChanges =
    editedPlateNumber.trim().toUpperCase() !==
    originalPlateNumber.toUpperCase();

  const isValidPlateFormat = INDIAN_PLATE_REGEX.test(
    editedPlateNumber.trim().toUpperCase()
  );

  const handleUpdatePlate = async () => {
    // Don't send request if no changes
    if (!hasChanges) {
      setUpdateError("No changes to update");
      return;
    }

    if (!editedPlateNumber.trim()) {
      setUpdateError("Please enter a valid plate number");
      return;
    }

    setIsUpdating(true);
    setUpdateError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/vehicles/${vehicle.vehicle_id}/plate`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            vehicle_number: editedPlateNumber.trim().toUpperCase(),
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update plate number");
      }

      const updatedVehicle = await response.json();

      // Update original to new value
      setOriginalPlateNumber(editedPlateNumber.trim().toUpperCase());

      // Call parent callback to update the vehicle list
      onVehicleUpdate(updatedVehicle);

      setSuccessMessage("✓ Plate updated successfully");
      setTimeout(() => setSuccessMessage(null), 3000);

      console.log("✓ Plate number updated successfully");
    } catch (error) {
      console.error("Error updating plate:", error);
      setUpdateError("Failed to update. Please try again.");
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="h-full bg-white rounded-lg shadow min-h-0 min-w-0 overflow-y-auto">
      <div className="p-6">
        {/* Vehicle Details */}
        <div className="mb-4">
          <h3 className="text-xl font-bold text-black mb-4 border-b border-gray-300 pb-1">
            Vehicle Details
          </h3>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Time</span>
              <span className="text-md text-black">
                {new Date(vehicle.timestamp).toLocaleString("en-IN", {
                  dateStyle: "short",
                  timeStyle: "medium",
                })}
              </span>
            </div>

            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Type</span>
              <span className="text-md text-black capitalize">
                {vehicle.vehicle_type || "N/A"}
              </span>
            </div>

            {vehicle.color !== "Unknown" && (
              <div className="flex justify-between">
                <span className="text-md font-semibold text-black">Colour</span>
                <span className="text-md text-black capitalize">
                  {vehicle.color}
                </span>
              </div>
            )}

            <div className="flex justify-between">
              <span className="text-md font-semibold text-black">Camera</span>
              <span className="text-md text-black">
                {formatLocation(vehicle.location)}
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
          </div>
        </div>

        {/* Plate Details Card */}
        <div className="mb-4 bg-gray-50 rounded-lg shadow-sm p-4 border border-gray-200">
          {/* Header with validation warning */}
          <div className="flex items-center justify-between mb-3 border-b border-gray-300 pb-2">
            <h3 className="text-lg font-bold text-black">Plate Details</h3>

            {/* Validation Warning Icon */}
            {editedPlateNumber && !isValidPlateFormat && (
              <div
                className="flex items-center gap-1 text-amber-600"
                title="Invalid plate format"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-xs font-medium">Invalid Format</span>
              </div>
            )}

            {/* Valid Format Checkmark */}
            {editedPlateNumber && isValidPlateFormat && (
              <div
                className="flex items-center gap-1 text-green-600"
                title="Valid plate format"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-xs font-medium">Valid</span>
              </div>
            )}
          </div>

          {/* Plate Image - Fixed Height & Centered */}
          <div className="relative flex items-center justify-center h-32 bg-white rounded border border-gray-200 mb-3 overflow-hidden">
            {vehicle.plate_url &&
            vehicle.vehicle_number &&
            vehicle.vehicle_number !== "N/A" ? (
              <Image
                src={vehicle.plate_url}
                alt="License Plate"
                fill
                className="rounded object-contain p-2"
              />
            ) : (
              <span className="text-gray-400 text-sm">No plate image</span>
            )}
          </div>

          {/* Always Editable Plate Number Input */}
          <input
            type="text"
            value={editedPlateNumber}
            onChange={(e) => {
              setEditedPlateNumber(e.target.value.toUpperCase());
              setUpdateError(null);
              setSuccessMessage(null);
              //  Notify parent that user is editing (only if on latest vehicle)
              if (onPlateEditStart && newValue !== originalPlateNumber) {
                onPlateEditStart();
              }
            }}
            placeholder="e.g., KL11BM2325"
            className={`w-full px-3 py-2 border rounded mb-2 text-sm text-center font-semibold focus:outline-none focus:ring-2 ${
              editedPlateNumber && !isValidPlateFormat
                ? "border-amber-400 focus:ring-amber-500"
                : "border-gray-300 focus:ring-blue-500"
            }`}
            disabled={isUpdating}
          />

          {/* Format Helper Text */}
          {editedPlateNumber && !isValidPlateFormat && (
            <p className="text-amber-600 text-xs mb-2 text-center">
              Expected format: AA00AA0000 (e.g., KL11BM2325)
            </p>
          )}

          {/* Error/Success Messages */}
          {updateError && (
            <p className="text-red-500 text-xs mb-2 text-center">
              {updateError}
            </p>
          )}
          {successMessage && (
            <p className="text-green-600 text-xs mb-2 text-center">
              {successMessage}
            </p>
          )}

          {/* Update Button */}
          <button
            onClick={handleUpdatePlate}
            disabled={isUpdating || !hasChanges}
            className={`w-full px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              hasChanges && !isUpdating
                ? "bg-gray-900 hover:bg-gray-800 text-white cursor-pointer"
                : "bg-gray-300 text-gray-500 cursor-not-allowed"
            }`}
          >
            {isUpdating
              ? "Updating..."
              : hasChanges
              ? "Update Plate"
              : "No Changes"}
          </button>

          {/* Optional: Show original value if changed */}
          {hasChanges && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Original: {originalPlateNumber || "N/A"}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
