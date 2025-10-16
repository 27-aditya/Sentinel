import { useState, useEffect, useRef } from "react";
import Image from "next/image";
import VehicleCard from "@/components/VehicleCard/VehicleCard";
import Filter from "@/components/Filter/Filter";

export default function SearchView() {
    const [filteredVehicles, setFilteredVehicles] = useState([]);
    const [selectedVehicle, setSelectedVehicle] = useState(null);
    const [formattedDate, setFormattedDate] = useState("");
    const [formattedTime, setFormattedTime] = useState("");
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState(""); 
    const [filterOptions, setFilterOptions] = useState({
        locations: [],
        vehicle_types: [],
        colors: []
    });
    const [isLoadingFilters, setIsLoadingFilters] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [appliedFilters, setAppliedFilters] = useState(null);
    const [isLoadingVehicles, setIsLoadingVehicles] = useState(false);
    const filterButtonRef = useRef(null);
    const searchDebounceRef = useRef(null);

    // Fetch filter options from API
    const fetchFilterOptions = async () => {
        try {
            setIsLoadingFilters(true);
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/filters`
            );

            if (!response.ok) {
                throw new Error("Failed to fetch filter options");
            }

            const data = await response.json();
            setFilterOptions(data);
            console.log("✓ Loaded filter options:", data);
        } catch (error) {
            console.error("Error fetching filter options:", error);
            // Set empty arrays as fallback
            setFilterOptions({
                locations: [],
                vehicle_types: [],
                colors: []
            });
        } finally {
            setIsLoadingFilters(false);
        }
    };

    // Load filter options on mount
    useEffect(() => {
        fetchFilterOptions();
    }, []);

    // Load today's vehicles on mount (initial default filter)
    useEffect(() => {
        // Create default filter for today
        const today = new Date();
        const todayString = today.toISOString().split('T')[0]; // YYYY-MM-DD format
        
        const defaultFilters = {
            location: "",
            date: todayString,
            startTime: "00:00",
            endTime: "23:59",
            color: "",
            vehicleType: ""
        };

        // Set as applied filters and fetch
        setAppliedFilters(defaultFilters);
        fetchVehicles(defaultFilters, 1);
        
        console.log(`✓ Loading today's vehicles (${todayString})`);
    }, []); // Empty dependency array - runs once on mount

    // Date Time Logic
    useEffect(() => {
        const interval = setInterval(() => {
            const now = new Date();
            setFormattedDate(
                now.toLocaleDateString("en-IN", {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                })
            );
            setFormattedTime(
                now.toLocaleTimeString("en-IN", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                })
            );
        }, 1000);

        return () => clearInterval(interval);
    }, []);

    const handleVehicleSelect = (vehicle) => {
        setSelectedVehicle(vehicle);
    };

    // Helper function to build query parameters from filters and search
    const buildQueryParams = (filters, page = 1, searchQuery = null) => {
        const params = new URLSearchParams();
        
        // Add filter parameters
        if (filters?.location) {
            params.append('location', filters.location);
        }
        if (filters?.date) {
            // Combine date with start/end time for proper filtering
            if (filters.startTime) {
                const startDateTime = `${filters.date}T${filters.startTime}:00`;
                params.append('start_date', startDateTime);
            } else {
                // If no start time, use beginning of day
                params.append('start_date', `${filters.date}T00:00:00`);
            }
            
            if (filters.endTime) {
                const endDateTime = `${filters.date}T${filters.endTime}:00`;
                params.append('end_date', endDateTime);
            } else {
                // If no end time, use end of day
                params.append('end_date', `${filters.date}T23:59:59`);
            }
        }
        if (filters?.color) {
            params.append('color', filters.color);
        }
        if (filters?.vehicleType) {
            params.append('vehicle_type', filters.vehicleType);
        }
        
        // Add search query if provided
        if (searchQuery) {
            params.append('plate_query', searchQuery);
        }
        
        // Add pagination parameters
        params.append('page', page.toString());
        params.append('page_size', '20');
        
        return params;
    };

    // Reusable function to fetch vehicles with filters and pagination
    const fetchVehicles = async (filters, page = 1, searchQuery = null) => {
        try {
            setIsLoadingVehicles(true);
            
            const params = buildQueryParams(filters, page, searchQuery);

            console.log(`Fetching vehicles - Page ${page} with params:`, params.toString());

            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/search?${params.toString()}`
            );

            if (!response.ok) {
                throw new Error('Failed to fetch filtered vehicles');
            }

            const data = await response.json();
            
            console.log(`✓ Loaded ${data.vehicles.length} vehicles - Page ${data.page}/${data.total_pages}`);
            
            // Update vehicles with filtered results
            setFilteredVehicles(data.vehicles);
            setCurrentPage(data.page);
            setTotalPages(data.total_pages);
            
            // Select first vehicle if results exist
            if (data.vehicles.length > 0) {
                setSelectedVehicle(data.vehicles[0]);
            } else {
                setSelectedVehicle(null);
            }
        } catch (error) {
            console.error('Error fetching filtered vehicles:', error);
            // Keep existing vehicles on error
        } finally {
            setIsLoadingVehicles(false);
        }
    };

    const handleApplyFilters = async (filters) => {
        // Save filters and fetch first page
        setAppliedFilters(filters);
        await fetchVehicles(filters, 1);
    };

    const handleNextPage = () => {
        if (currentPage < totalPages) {
            fetchVehicles(appliedFilters, currentPage + 1);
        }
    };

    const handlePreviousPage = () => {
        if (currentPage > 1) {
            fetchVehicles(appliedFilters, currentPage - 1);
        }
    };

    // Debounced search function
    const handleSearch = (query) => {
        setSearchQuery(query);
        
        // Clear existing debounce timer
        if (searchDebounceRef.current) {
            clearTimeout(searchDebounceRef.current);
        }

        // If query is empty, reset to show all filtered vehicles or original vehicles
        if (!query.trim()) {
            // If filters are applied, re-fetch with filters, otherwise show original vehicles
            if (appliedFilters) {
                fetchVehicles(appliedFilters, 1);
            } else {
                setFilteredVehicles(vehicles);
                if (vehicles.length > 0) {
                    setSelectedVehicle(vehicles[0]);
                }
            }
            return;
        }

        // Set new debounce timer (500ms delay)
        searchDebounceRef.current = setTimeout(() => {
            // Use the unified fetchVehicles function with search query
            fetchVehicles(appliedFilters, 1, query);
        }, 500); // 500ms debounce delay
    };

    // Cleanup debounce on unmount
    useEffect(() => {
        return () => {
            if (searchDebounceRef.current) {
                clearTimeout(searchDebounceRef.current);
            }
        };
    }, []);

    return ( 
    <div className="h-full flex flex-col">

        {/* Header */}
        <div className="bg-gray-200 px-6 pt-6 flex justify-between items-start">
            <h1 className="text-4xl font-semibold text-gray-900">
                Search & Filter
            </h1>

            <div className="text-right">
                <div className="text-gray-700 text-md font-medium">
                    {formattedDate}
                </div>
                <div className="text-gray-500 text-sm">{formattedTime}</div>
            </div>
        </div>
        
         
        {/* content */}
        <div className="flex-1 bg-gray-200 px-auto md:px-6 flex md:flex-row flex-col p-6 pt-4 gap-4 min-h-0 overflow-auto">
            
            {/*filtering section*/}
            <div className= "flex flex-1 bg-white md:p-4 flex-col min-h-0 min-w-0 rounded-lg shadow relative" >
                
                {/* Top section */}
                <div className="flex h-[50px] gap-2 mb-2 relative">
                    <button 
                        ref={filterButtonRef}
                        onClick={() => setIsFilterOpen(true)}
                        className="px-4 py-2 bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors flex items-center gap-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                        </svg>
                        Filter
                    </button>
                    
                    {/* Filter Modal */}
                    <Filter 
                        isOpen={isFilterOpen}
                        onClose={() => setIsFilterOpen(false)}
                        onApplyFilters={handleApplyFilters}
                        buttonRef={filterButtonRef}
                        filterOptions={filterOptions}
                        isLoading={isLoadingFilters}
                        appliedFilters={appliedFilters}
                    />

                    <input 
                        type="text" 
                        placeholder="Search by plate number..." 
                        value={searchQuery}
                        onChange={(e) => handleSearch(e.target.value)}
                        className="w-[30%] px-4 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-900"
                    />
                </div>
                
                {/* vehicle cards render */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                    {isLoadingVehicles ? (
                        <div className="text-center text-gray-500 py-8">
                            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-gray-400 mx-auto mb-2"></div>
                            Loading vehicles...
                        </div>
                    ) : filteredVehicles.length === 0 ? (
                        <div className="text-center text-gray-500 py-8">
                            No vehicles found
                        </div>
                    ) : (
                        filteredVehicles.map((vehicle) => (
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
                
                {/*pagination component*/}
                {totalPages > 1 && (
                    <div className="flex items-center justify-center gap-4 py-4 border-t border-gray-200">
                        <button 
                            onClick={handlePreviousPage}
                            disabled={currentPage === 1 || isLoadingVehicles}
                            className="px-4 py-1 bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        
                        <div className="flex items-center gap-2 text-gray-700">
                            <span className="font-medium">{currentPage}</span>
                            <span>/</span>
                            <span>{totalPages}</span>
                        </div>
                        
                        <button 
                            onClick={handleNextPage}
                            disabled={currentPage === totalPages || isLoadingVehicles}
                            className="px-4 py-1 bg-gray-900 text-white rounded hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                )}

            </div>
            
            <div className="w-full md:w-[30%] md:h-full overflow-y-auto">
                
                {/* vehicle image */}
                <div className="h-[250px] mb-4 md:min-h-0 flex items-center justify-center relative bg-black rounded">
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
                            <p>Select a vehicle to view details</p>
                        </div>
                    )}
                </div>
                
                
                {/* Vehicle Information Panel */}
                {/* need to make this into a compontn */}
                <div className="flex-1 bg-white rounded-lg shadow overflow-y-auto">
                    {selectedVehicle ? (
                        <div className="p-6">
                            <h3 className="text-xl font-bold text-black mb-4 border-b border-gray-300 pb-2">
                                Vehicle Details
                            </h3>

                            <div className="space-y-3">

                                <div className="flex justify-between">
                                    <span className="text-sm font-semibold text-gray-700">Plate Number:</span>
                                    <span className="text-sm text-gray-900 font-mono">{selectedVehicle.vehicle_number || "N/A"}</span>
                                </div>

                                <div className="flex justify-between">
                                    <span className="text-sm font-semibold text-gray-700">Time:</span>
                                    <span className="text-sm text-gray-900">
                                        {selectedVehicle.timestamp ? new Date(selectedVehicle.timestamp).toLocaleString("en-IN", {
                                            dateStyle: "short",
                                            timeStyle: "medium",
                                        }) : "N/A"}
                                    </span>
                                </div>

                                <div className="flex justify-between">
                                    <span className="text-sm font-semibold text-gray-700">Type:</span>
                                    <span className="text-sm text-gray-900 capitalize">{selectedVehicle.vehicle_type || "N/A"}</span>
                                </div>

                                <div className="flex justify-between">
                                    <span className="text-sm font-semibold text-gray-700">Color:</span>
                                    <div className="flex items-center gap-2">
                                        {selectedVehicle.color_hex && (
                                            <div 
                                                className="w-4 h-4 rounded border border-gray-300" 
                                                style={{ backgroundColor: selectedVehicle.color_hex }}
                                            ></div>
                                        )}
                                        <span className="text-sm text-gray-900 capitalize">{selectedVehicle.color || "N/A"}</span>
                                    </div>
                                </div>

                                <div className="flex justify-between">
                                    <span className="text-sm font-semibold text-gray-700">Location:</span>
                                    <span className="text-sm text-gray-900">
                                        {selectedVehicle.location ? selectedVehicle.location.split("_").map(word => 
                                            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                                        ).join(" ") : "N/A"}
                                    </span>
                                </div>

                                {selectedVehicle.model && (
                                    <div className="flex justify-between">
                                        <span className="text-sm font-semibold text-gray-700">Make/Model:</span>
                                        <span className="text-sm text-gray-900">{selectedVehicle.model}</span>
                                    </div>
                                )}

                                {/* Plate Image */}
                                {selectedVehicle.plate_url && (
                                    <div className="mt-4 pt-4 border-t border-gray-200">
                                        <h4 className="text-sm font-semibold text-gray-700 mb-2">Plate Image:</h4>
                                        <div className="relative h-24 bg-gray-100 rounded border border-gray-200 overflow-hidden">
                                            <Image
                                                src={selectedVehicle.plate_url}
                                                alt="License Plate"
                                                fill
                                                className="object-contain p-2"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="p-6 text-center text-gray-500">
                            Select a vehicle to view details
                        </div>
                    )}
                </div>

            </div>
        </div>
    </div>
    )
}