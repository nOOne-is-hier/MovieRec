"use client";
import React, { useState, useEffect, ChangeEvent } from "react";
import api from "../../lib/api";

const genres = [
  "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
  "Drama", "Family", "Fantasy", "History", "Horror", "Music",
  "Mystery", "Romance", "Sci-Fi", "TV Movie", "Thriller", "War", "Western",
];

export default function ProfileSettingsPage() {
  const [userId, setUserId] = useState<number | null>(null);
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const [originalProfileImage, setOriginalProfileImage] = useState<string | null>(null);
  const [username, setUsername] = useState("");
  const [originalUsername, setOriginalUsername] = useState("");
  const [bio, setBio] = useState("");
  const [originalBio, setOriginalBio] = useState("");
  const [favoriteGenres, setFavoriteGenres] = useState<string[]>([]);
  const [originalFavoriteGenres, setOriginalFavoriteGenres] = useState<string[]>([]);
  const [bioError, setBioError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  // 사용자 정보 로드
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        // 새로운 엔드포인트로 변경
        const userResponse = await api.get("/accounts/users/me/edit-profile/");
        const { id, username, bio, favorite_genres, profile_image } = userResponse.data;
        setUserId(id);
        setUsername(username || "");
        setOriginalUsername(username || "");
        setBio(bio || "");
        setOriginalBio(bio || "");
        setFavoriteGenres(favorite_genres || []);
        setOriginalFavoriteGenres(favorite_genres || []);
        setProfileImage(profile_image || null);
        setOriginalProfileImage(profile_image || null);

        // userId 설정 확인
        console.log("Initial userId set:", id);
      } catch (error) {
        console.error("Error fetching profile:", error);
        setSaveMessage("Failed to load profile. Please try again.");
      }
    };
    fetchProfile();
  }, []);

  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfileImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleBioChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    const newBio = event.target.value;
    setBio(newBio);
    setBioError(newBio.length > 500 ? "Bio must not exceed 500 characters" : "");
  };

  const handleGenreToggle = (genre: string) => {
    setFavoriteGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
  };

  const base64ToFile = (base64Data: string, fileName: string): File => {
    if (!base64Data.includes(",")) throw new Error("Invalid Base64 format");
    const [header, data] = base64Data.split(",");
    const mimeMatch = header.match(/:(.*?);/);
    if (!mimeMatch) throw new Error("Invalid MIME type in Base64 data");
    const mime = mimeMatch[1];
    const bstr = atob(data);
    const u8arr = new Uint8Array(bstr.length);
    for (let i = 0; i < bstr.length; i++) {
      u8arr[i] = bstr.charCodeAt(i);
    }
    return new File([u8arr], fileName, { type: mime });
  };

  const handleSave = async () => {
    console.log("Current userId when saving:", userId);

    if (!userId) {
      setSaveMessage("User ID not found. Please try again.");
      return;
    }
    if (bio.length > 500) {
      setBioError("Please shorten your bio to 500 characters or less before saving.");
      return;
    }

    const updatedFields: Record<string, any> = {};
    if (username !== originalUsername) updatedFields.username = username;
    if (bio !== originalBio) updatedFields.bio = bio;
    if (JSON.stringify(favoriteGenres) !== JSON.stringify(originalFavoriteGenres)) {
      updatedFields.favorite_genres = favoriteGenres;
    }
    
    if (profileImage !== originalProfileImage) {
      if (profileImage && !profileImage.startsWith("data:image/")) {
        setSaveMessage("Invalid profile image format. Please upload a valid image.");
        return;
      }
      const imageFile =
        profileImage ? base64ToFile(profileImage, "profile_image.webp") : null;
      updatedFields.profile_image = imageFile;
    }

    try {
      const formData = new FormData();
      Object.entries(updatedFields).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach((v) => formData.append(key, v));
        } else if (value !== null) {
          formData.append(key, value);
        }
      });

      const response = await api.patch(
        `accounts/users/me/edit-profile/update/`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setSaveMessage("Settings saved successfully!");
      console.log("Response:", response.data);

      // 상태 동기화
      setOriginalUsername(username);
      setOriginalBio(bio);
      setOriginalFavoriteGenres(favoriteGenres);
      setOriginalProfileImage(profileImage);

    } catch (error: any) {
      console.error("Error saving settings:", error);

      if (error.response && error.response.data) {
        setSaveMessage(
          error.response.data.message ||
          error.response.data.username?.[0] ||
          "Failed to save settings. Please check your inputs."
        );
      } else {
        setSaveMessage("Network error. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl bg-gray-800 text-gray-100 rounded-lg shadow-lg p-6 space-y-6">
        <h2 className="text-2xl font-bold text-center">Member Settings</h2>
        
        <div className="flex flex-col items-center">
          <div className="w-24 h-24 rounded-full overflow-hidden bg-gray-700 mb-4 flex items-center justify-center text-gray-500">
            {profileImage ? (
              <img src={profileImage} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              "No Image"
            )}
          </div>
          <label className="cursor-pointer bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition duration-300">
            <input type="file" className="hidden" onChange={handleImageUpload} accept="image/*" />
            Upload Picture
          </label>
        </div>

        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
            Username
          </label>
          <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        <div>
          <label htmlFor="bio" className="block text-sm font-medium text-gray-300 mb-1">
            Bio 
          </label>
          <textarea id="bio" rows={4} value={bio} onChange={handleBioChange}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-gray-200 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Write a brief bio about yourself"
          ></textarea>
          <p className="text-sm text-gray-400 mt-1">{bio.length}/500 characters</p>
          {bioError && <p className="text-sm text-red-400 mt-1">{bioError}</p>}
        </div>

        <div>
          <h3 className="text-lg font-medium text-gray-200 mb-3">Favorite Genres</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {genres.map((genre) => (
              <label key={genre} className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox h-5 w-5 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500 focus:ring-offset-gray-800"
                  checked={favoriteGenres.includes(genre)} onChange={() => handleGenreToggle(genre)}
                />
                <span className="ml-2 text-gray-300">{genre}</span>
              </label>
            ))}
          </div>
        </div>

        <button onClick={handleSave} className="w-full bg-purple-600 text-white py-2 rounded hover:bg-purple-700 transition duration-300">
          Save Settings 
        </button>

        {saveMessage && (
          <p className={`mt-4 text-center ${saveMessage.includes("Failed") ? "text-red-400" : "text-green-400"}`}>
            {saveMessage}
          </p>
        )}
        
      </div>
    </div>
  );
}