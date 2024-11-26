"use client";
import React, { useState, useEffect, ChangeEvent } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import api from "@/lib/api";

const genres = [
  "액션", "모험", "애니메이션", "코미디", "범죄", "다큐멘터리",
  "드라마", "가족", "판타지", "역사", "공포", "음악",
  "미스터리", "로맨스", "SF", "TV 영화", "스릴러", "전쟁", "서부",
];

const genreMap: { [key: string]: number } = {
  "액션": 1, "모험": 2, "애니메이션": 3, "코미디": 4, "범죄": 5,
  "다큐멘터리": 6, "드라마": 7, "가족": 8, "판타지": 9, "역사": 10,
  "공포": 11, "음악": 12, "미스터리": 13, "로맨스": 14, "SF": 15,
  "TV 영화": 16, "스릴러": 17, "전쟁": 18, "서부": 19,
};

interface ProfileSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: number;
}

export function ProfileSettingsModal({ isOpen, onClose, userId }: ProfileSettingsModalProps) {
  const [profileImage, setProfileImage] = useState<string | null>(null);
  const [originalProfileImage, setOriginalProfileImage] = useState<string | null>(null);
  const [bio, setBio] = useState("");
  const [originalBio, setOriginalBio] = useState("");
  const [favoriteGenres, setFavoriteGenres] = useState<string[]>([]);
  const [originalFavoriteGenres, setOriginalFavoriteGenres] = useState<string[]>([]);
  const [bioError, setBioError] = useState("");
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => {
    const fetchProfile = async () => {
        try {
          const userResponse = await api.get("/accounts/users/me/edit-profile/");
          const { bio, favorite_genres, profile_image } = userResponse.data;
      
          setBio(bio || "");
          setOriginalBio(bio || "");
          setFavoriteGenres(favorite_genres || []);
          setOriginalFavoriteGenres(favorite_genres || []);
      
          // `api` 인스턴스의 baseURL 활용
          const absoluteProfileImage = profile_image
            ? profile_image.startsWith("http")
              ? profile_image // 절대 경로인 경우 그대로 사용
              : `${api.defaults.baseURL}${profile_image}` // 상대 경로인 경우 baseURL과 합침
            : null;
      
          setProfileImage(absoluteProfileImage);
          setOriginalProfileImage(absoluteProfileImage);
        } catch (error) {
          console.error("Error fetching profile:", error);
          setSaveMessage("Failed to load profile. Please try again.");
        }
      };
      

    if (isOpen) {
      fetchProfile();
    }
  }, [isOpen]);

  const handleImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        setProfileImage(result);
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

  const handleSave = async () => {
    if (bio.length > 500) {
      setBioError("Please shorten your bio to 500 characters or less before saving.");
      return;
    }

    const updatedFields: Record<string, any> = {};
    if (bio !== originalBio) updatedFields.bio = bio;
    if (JSON.stringify(favoriteGenres) !== JSON.stringify(originalFavoriteGenres)) {
      const genreIds = favoriteGenres.map((genre) => {
        const genreId = genreMap[genre];
        if (genreId === undefined) {
          console.error(`Invalid genre detected: '${genre}' does not exist in genreMap.`);
          return null;
        }
        return genreId;
      }).filter((id) => id !== null);

      updatedFields.favorite_genres_ids = genreIds;
    }

    if (profileImage && profileImage !== originalProfileImage) {
      const file = await base64ToFile(profileImage, "profile_image.webp");
      updatedFields.profile_image = file;
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
      setOriginalBio(bio);
      setOriginalFavoriteGenres(favoriteGenres);
      setOriginalProfileImage(profileImage);
    } catch (error: any) {
      console.error("Error saving settings:", error);
      setSaveMessage("Failed to save settings. Please check your inputs.");
    }
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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] bg-[#1a1a1a] text-white border-0">
        <DialogHeader>
          <DialogTitle>Profile Settings</DialogTitle>
        </DialogHeader>
        <div className="grid gap-6 py-4">
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 rounded-full overflow-hidden bg-[#2a2a2a] mb-4">
              {profileImage ? (
                <img
                  src={profileImage}
                  alt="Profile"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-500">
                  No Image
                </div>
              )}
            </div>
            <label className="cursor-pointer bg-[#8b5cf6] text-white px-6 py-2 rounded hover:bg-[#7c3aed] transition duration-300">
              <input type="file" className="hidden" onChange={handleImageUpload} accept="image/*" />
              Upload Picture
            </label>
          </div>
          {/* Bio Input */}
          <div className="grid gap-2">
            <label htmlFor="bio" className="text-sm font-medium text-gray-300">
              Bio
            </label>
            <Textarea
              id="bio"
              rows={4}
              value={bio}
              onChange={handleBioChange}
              className="bg-[#2a2a2a] border-0 text-gray-200 resize-none"
              placeholder="Write a brief bio about yourself"
            />
            <p className="text-sm text-gray-400">{bio.length}/500 characters</p>
            {bioError && <p className="text-sm text-red-400">{bioError}</p>}
          </div>

          {/* Favorite Genres */}
          <div className="grid gap-2">
            <h3 className="text-lg font-medium text-gray-200">Favorite Genres</h3>
            <div className="grid grid-cols-2 gap-x-8 gap-y-2">
              {genres.map((genre) => (
                <label key={genre} className="flex items-center space-x-2">
                  <Checkbox
                    checked={favoriteGenres.includes(genre)}
                    onCheckedChange={() => handleGenreToggle(genre)}
                    className="border-gray-600"
                  />
                  <span className="text-gray-300">{genre}</span>
                </label>
              ))}
            </div>
          </div>

          <Button
            onClick={handleSave}
            className="w-full bg-[#8b5cf6] hover:bg-[#7c3aed] text-white border-0"
          >
            Save Settings
          </Button>

          {saveMessage && (
            <p className={`text-center ${saveMessage.includes("Failed") ? "text-red-400" : "text-green-400"}`}>
              {saveMessage}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
