import { useState, useEffect } from "react";

export default function Filter({ isOpen, onClose, onApplyFilters, buttonRef, filterOptions, isLoading , appliedFilters }) {
  const [filters, setFilters] = useState({
    location: "",
    date: "",
    startTime: "",
    endTime: "",
    color: "",
    vehicleType: "",
  });

  // Sync filters with appliedFilters when it changes
  useEffect(() => {
    if (appliedFilters) {
      setFilters({
        location: appliedFilters.location || "",
        date: appliedFilters.date || "",
        startTime: appliedFilters.startTime || "",
        endTime: appliedFilters.endTime || "",
        color: appliedFilters.color || "",
        vehicleType: appliedFilters.vehicleType || "",
      });
    }
  }, [appliedFilters]);

  // Close modal when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (isOpen && buttonRef?.current && !buttonRef.current.contains(e.target)) {
        const modal = document.getElementById('filter-modal');
        if (modal && !modal.contains(e.target)) {
          onClose();
        }
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose, buttonRef]);

  const handleInputChange = (field, value) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleApply = () => {
    onApplyFilters(filters);
    onClose();
  };

  const handleClear = () => {
    setFilters({
      location: "",
      date: "",
      startTime: "",
      endTime: "",
      color: "",
      vehicleType: "",
    });
  };

  if (!isOpen) return null;

  return (
      <div 
        id="filter-modal"
        className="absolute top-full left-0 mt-2 bg-white rounded-lg shadow-2xl w-full max-w-2xl p-6 z-50 border border-gray-200"
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">Filter Vehicles</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
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
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Filter Grid - 2 Columns */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Location */}
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <select
              value={filters.location}
              onChange={(e) => handleInputChange("location", e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
              disabled={isLoading}
            >
              <option value="">
                {isLoading ? "Loading locations..." : "All Locations"}
              </option>
              {filterOptions?.locations?.map((location) => (
                <option key={location.id} value={location.name}>
                  {location.name}
                </option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date
            </label>
            <input
              type="date"
              value={filters.date}
              onChange={(e) => handleInputChange("date", e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
            />
          </div>

          {/* Start Time */}
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Time
            </label>
            <input
              type="time"
              value={filters.startTime}
              onChange={(e) => handleInputChange("startTime", e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
            />
          </div>

          {/* End Time */}
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Time
            </label>
            <input
              type="time"
              value={filters.endTime}
              onChange={(e) => handleInputChange("endTime", e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
            />
          </div>

          {/* Color */}
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Color
            </label>
            <select
              value={filters.color}
              onChange={(e) => handleInputChange("color", e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
              disabled={isLoading}
            >
              <option value="">
                {isLoading ? "Loading colors..." : "All Colors"}
              </option>
              {filterOptions?.colors?.map((color) => (
                <option key={color.id} value={color.name}>
                  {color.name}
                </option>
              ))}
            </select>
          </div>

          {/* Vehicle Type */}
          <div className="col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Vehicle Type
            </label>
            <select
              value={filters.vehicleType}
              onChange={(e) => handleInputChange("vehicleType", e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
              disabled={isLoading}
            >
              <option value="">
                {isLoading ? "Loading types..." : "All Types"}
              </option>
              {filterOptions?.vehicle_types?.map((type) => (
                <option key={type.id} value={type.name}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3">
          <button
            onClick={handleClear}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors"
          >
            Clear All
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleApply}
            className="px-6 py-2 bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors"
          >
            Apply Filters
          </button>
        </div>
      </div>
  );
}
