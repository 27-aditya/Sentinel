import Image from "next/image";

export default function DetailedInfo({ vehicle }) {
  return (
    <div className="h-full bg-white overflow-y-auto">
      <div className="border border-gray-300 rounded-lg p-6">
        
        {/* Transaction Details */}
        <div className="mb-6">
          <h3 className="text-[15px] font-bold text-black mb-4 border-b border-gray-300 pb-3">
            Transaction Details
          </h3>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-[13px] font-semibold text-black">Time</span>
              <span className="text-[13px] text-black">{vehicle?.timeStamp || "2025-08-08 17:50:02"}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-[13px] font-semibold text-black">Camera</span>
              <span className="text-[13px] text-black">{vehicle?.cameraLocation || "ELATHUR TO KKD"}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-[13px] font-semibold text-black">Junction</span>
              <span className="text-[13px] text-black">ELATHUR_JN</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-[13px] font-semibold text-black">Project</span>
              <span className="text-[13px] text-black">KOZHIKODE</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-[13px] font-semibold text-black">GPS</span>
              <span className="text-[13px] text-black">11.352214, 75.740565</span>
            </div>
            
            {/* <div className="flex justify-between">
              <span className="text-[13px] font-semibold text-black">Violation ID</span>
              <span className="text-[13px] text-black">P08C180-2025080815188</span>
            </div> */}
            
            <div className="flex justify-between">
              <span className="text-[13px] font-semibold text-black">Status</span>
              <span className="text-[13px] text-black">{vehicle?.status || "New"}</span>
            </div>
          </div>
        </div>

        {/* Other Details */}
        {/* <div className="mb-4">
          <h3 className="text-sm font-bold text-gray-800 mb-3 border-b border-gray-300 pb-2">
            Other Details
          </h3>
          
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <input 
                type="checkbox" 
                id="showReference" 
                className="w-3 h-3"
              />
              <label htmlFor="showReference" className="text-xs text-gray-700">
                Show Reference Image
              </label>
            </div>
            
            <div>
              <span className="text-xs font-semibold text-gray-700 block mb-1">
                Challan Remarks
              </span>
              <textarea 
                className="w-full border border-gray-300 rounded p-2 text-xs text-gray-900"
                rows="3"
                placeholder="Enter remarks..."
              />
            </div>
          </div>
        </div> */}

        {/* Vehicle Number Plate Image */}
        <div className="mb-6">
          <h3 className="text-[15px] font-bold text-black mb-4 border-b border-gray-300 pb-3">
            Vehicle Number Plate Image
          </h3>
          
          {vehicle?.licensePlateImage ? (
            <Image 
              src={vehicle.licensePlateImage}
              alt="License Plate"
              width={250}
              height={75}
              className="border border-gray-300 rounded"
            />
          ) : (
            <div className="w-full h-20 border border-gray-300 rounded flex items-center justify-center text-[13px] text-black">
              No image available
            </div>
          )}
        </div>

        {/* Vehicle Registration Number */}
        <div>
          <h3 className="text-[15px] font-bold text-black mb-4 border-b border-gray-300 pb-3">
            Vehicle Registration Number
          </h3>
          
          <input 
            type="text"
            value={vehicle?.regNumber || "KL71J3583"}
            readOnly
            className="w-full border border-gray-300 rounded p-3 text-[13px] text-black bg-gray-50"
          />
        </div>

      </div>
    </div>
  );
}
