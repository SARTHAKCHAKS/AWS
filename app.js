// frontend/app.js

const API_BASE_URL = "YOUR_API_GATEWAY_BASE_URL";

const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const statusText = document.getElementById("status");
const fileList = document.getElementById("fileList");

uploadBtn.addEventListener("click", uploadFile);

async function uploadFile() {
  const file = fileInput.files[0];

  if (!file) {
    statusText.textContent = "Please select a file first.";
    return;
  }

  try {
    statusText.textContent = "Generating upload URL...";

    const urlResponse = await fetch(`${API_BASE_URL}/generate-upload-url`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        fileName: file.name,
        fileType: file.type
      })
    });

    const urlData = await urlResponse.json();

    if (!urlResponse.ok) {
      throw new Error(urlData.error || "Failed to generate upload URL");
    }

    statusText.textContent = "Uploading file to S3...";

    const uploadResponse = await fetch(urlData.uploadUrl, {
      method: "PUT",
      headers: {
        "Content-Type": file.type
      },
      body: file
    });

    if (!uploadResponse.ok) {
      throw new Error("S3 upload failed");
    }

    statusText.textContent = "File uploaded successfully.";
    fileInput.value = "";
    loadFiles();
  } catch (error) {
    statusText.textContent = `Error: ${error.message}`;
  }
}

async function loadFiles() {
  try {
    const response = await fetch(`${API_BASE_URL}/files`);
    const files = await response.json();

    fileList.innerHTML = "";

    if (!files.length) {
      fileList.innerHTML = "<p>No files uploaded yet.</p>";
      return;
    }

    files.forEach(file => {
      const item = document.createElement("div");
      item.className = "file-item";

      item.innerHTML = `
        <div class="file-info">
          <strong>${file.fileName}</strong>
          <span>${file.fileType}</span>
          <small>${new Date(file.uploadedAt).toLocaleString()}</small>
        </div>
        <div class="file-actions">
          <a href="${file.fileUrl}" target="_blank">
            <button>View</button>
          </a>
          <button onclick="deleteFile('${file.id}')">Delete</button>
        </div>
      `;

      fileList.appendChild(item);
    });
  } catch (error) {
    fileList.innerHTML = `<p>Error loading files: ${error.message}</p>`;
  }
}

async function deleteFile(fileId) {
  try {
    const response = await fetch(`${API_BASE_URL}/files/${fileId}`, {
      method: "DELETE"
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Delete failed");
    }

    loadFiles();
  } catch (error) {
    alert(error.message);
  }
}

loadFiles();
