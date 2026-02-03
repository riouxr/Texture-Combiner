#!/usr/bin/env python3
"""
ORM Texture Combiner
Combines three texture maps into a single ORM texture:
- Red channel from AO/Occlusion map
- Green channel from Roughness map
- Blue channel from Metallic map

Automatically detects common texture suffixes (case-insensitive)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image
import os
import re
import shutil

class ORMCombiner:
    # Define suffix patterns for each texture type (case-insensitive)
    AO_SUFFIXES = ['_AO', '_ao', '_O', '_o', '_OCC', '_occ', '_Occlusion', '_occlusion', '_ambientocclusion']
    ROUGH_SUFFIXES = ['_ROUGH', '_rough', '_R', '_r', '_Roughness', '_roughness', '_GLOSS', '_gloss', '_Glossiness']
    METAL_SUFFIXES = ['_METAL', '_metal', '_MET', '_met', '_M', '_m', '_Metallic', '_metallic', '_Metalness', '_metalness']
    ALBEDO_SUFFIXES = ['_ALBEDO', '_albedo', '_BaseColor', '_basecolor', '_BC', '_bc', '_Diffuse', '_diffuse', '_Color', '_color', '_COL', '_col', '_ALB', '_alb']
    NORMAL_SUFFIXES = ['_NORMAL', '_normal', '_NormalMap', '_normalmap', '_NORM', '_norm', '_NRM', '_nrm', '_N', '_n']
    HEIGHT_SUFFIXES = ['_HEIGHT', '_height', '_Displacement', '_displacement', '_DISP', '_disp', '_DISPLACE', '_displace', '_H', '_h', '_D', '_d']
    
    def __init__(self, root):
        self.root = root
        self.root.title("ORM Texture Combiner - Batch Mode")
        self.root.geometry("800x650")  # Increased height from 600 to 650
        
        # Store file groups by base name
        # Structure: {base_name: {'AO': path, 'ROUGH': path, 'METAL': path, 'ALBEDO': path, 'NORMAL': path, 'HEIGHT': path}}
        self.file_groups = {}
        
        # Settings
        self.ignore_missing = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Title
        title = ttk.Label(self.root, text="ORM Texture Combiner - Batch Mode", 
                         font=('Arial', 16, 'bold'))
        title.pack(pady=(10, 5))  # Reduced bottom padding
        
        # Instructions
        instructions = ttk.Label(self.root, 
                                text="Drag and drop texture files (AO, Roughness, Metallic, Albedo, Normal, Height)\n" +
                                     "Files will be grouped by base name and processed in batch",
                                justify='center')
        instructions.pack(pady=(0, 5))  # Reduced padding
        
        # Drop zone frame
        drop_frame_container = tk.Frame(self.root)
        drop_frame_container.pack(pady=(5, 10), padx=20, fill=tk.BOTH, expand=True)  # Reduced top padding
        
        # Drop zone
        self.drop_frame = tk.Frame(drop_frame_container, bg='#e0e0e0', 
                                   relief=tk.SUNKEN, bd=2, height=120)  # Reduced from 150 to 120
        self.drop_frame.pack(fill=tk.X, pady=(0, 10))
        self.drop_frame.pack_propagate(False)
        
        # Enable drag and drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        drop_label = ttk.Label(self.drop_frame, 
                              text="📁 Drop texture files here\n(or entire folders)",
                              background='#e0e0e0',
                              font=('Arial', 12))
        drop_label.pack(expand=True)
        
        # File list with scrollbar
        list_label = ttk.Label(drop_frame_container, text="Detected texture sets:")
        list_label.pack(anchor='w')
        
        list_frame = tk.Frame(drop_frame_container)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, 
                                       yscrollcommand=scrollbar.set,
                                       font=('Courier', 9),
                                       height=12)  # Reduced from 15 to 12
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Status bar
        self.status_label = ttk.Label(self.root, text="Ready. Drop files to begin.", 
                                     relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # Button frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, pady=10)
        
        # Clear button
        self.clear_btn = ttk.Button(button_frame, text="Clear All", 
                                    command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Combine button
        self.combine_btn = ttk.Button(button_frame, text="Combine All Textures", 
                                     command=self.combine_all_textures,
                                     state='disabled')
        self.combine_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings frame
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(side=tk.BOTTOM, pady=5)
        
        # Ignore Missing checkbox
        ignore_check = ttk.Checkbutton(settings_frame, 
                                       text="Ignore Missing (process incomplete sets)",
                                       variable=self.ignore_missing,
                                       command=self.update_button_state)
        ignore_check.pack()
        
    def on_drop(self, event):
        # Get dropped files
        files = self.root.tk.splitlist(event.data)
        
        added_count = 0
        
        for file_path in files:
            # Remove curly braces if present (Windows sometimes adds them)
            file_path = file_path.strip('{}')
            
            # Handle directories - recursively find image files
            if os.path.isdir(file_path):
                for root, dirs, filenames in os.walk(file_path):
                    for filename in filenames:
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tga', '.tiff')):
                            full_path = os.path.join(root, filename)
                            if self.add_file(full_path):
                                added_count += 1
            elif os.path.isfile(file_path):
                if self.add_file(file_path):
                    added_count += 1
        
        if added_count > 0:
            self.update_file_list()
            self.status_label.config(text=f"Added {added_count} file(s). Ready to combine.")
        
        # Update button state based on ignore_missing setting
        self.update_button_state()
    
    def add_file(self, file_path):
        """Add a file to the appropriate group based on its texture type"""
        filename = os.path.basename(file_path)
        
        # Detect texture type
        texture_type, base_name = self.detect_texture_type(filename)
        
        if texture_type and base_name:
            # Create group if it doesn't exist
            if base_name not in self.file_groups:
                self.file_groups[base_name] = {
                    'AO': None, 
                    'ROUGH': None, 
                    'METAL': None,
                    'ALBEDO': None,
                    'NORMAL': None,
                    'HEIGHT': None
                }
            
            # Add file to group
            self.file_groups[base_name][texture_type] = file_path
            return True
        
        return False
    
    def update_file_list(self):
        """Update the listbox with current file groups"""
        self.file_listbox.delete(0, tk.END)
        
        for base_name in sorted(self.file_groups.keys()):
            group = self.file_groups[base_name]
            
            # Create status indicators for ORM maps
            ao_status = "✓" if group['AO'] else "✗"
            rough_status = "✓" if group['ROUGH'] else "✗"
            metal_status = "✓" if group['METAL'] else "✗"
            
            # Create status indicators for additional maps
            albedo_status = "✓" if group['ALBEDO'] else " "
            normal_status = "✓" if group['NORMAL'] else " "
            height_status = "✓" if group['HEIGHT'] else " "
            
            # Check if ORM set is complete
            orm_complete = all([group['AO'], group['ROUGH'], group['METAL']])
            
            status_str = f"[{ao_status}AO {rough_status}R {metal_status}M] [{albedo_status}A {normal_status}N {height_status}D]"
            
            if orm_complete:
                display_text = f"{status_str} ✓ {base_name}"
                self.file_listbox.insert(tk.END, display_text)
                self.file_listbox.itemconfig(tk.END, fg='green')
            else:
                display_text = f"{status_str}   {base_name}"
                self.file_listbox.insert(tk.END, display_text)
                self.file_listbox.itemconfig(tk.END, fg='orange')
    
    def has_complete_sets(self):
        """Check if we have at least one complete ORM texture set"""
        for group in self.file_groups.values():
            if all([group['AO'], group['ROUGH'], group['METAL']]):
                return True
        return False
    
    def update_button_state(self):
        """Update the combine button state based on ignore_missing setting"""
        if self.ignore_missing.get():
            # Enable if we have any files at all
            if self.file_groups:
                self.combine_btn.config(state='normal')
            else:
                self.combine_btn.config(state='disabled')
        else:
            # Enable only if we have complete sets
            if self.has_complete_sets():
                self.combine_btn.config(state='normal')
            else:
                self.combine_btn.config(state='disabled')
    
    def clear_all(self):
        """Clear all loaded files"""
        self.file_groups.clear()
        self.file_listbox.delete(0, tk.END)
        self.update_button_state()
        self.status_label.config(text="Cleared. Ready to drop files.")
    
    def detect_texture_type(self, filename):
        """Detect texture type based on filename suffix"""
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Check each suffix type (case-insensitive)
        for suffix in self.AO_SUFFIXES:
            if name_without_ext.lower().endswith(suffix.lower()):
                return 'AO', name_without_ext[:-len(suffix)]
        
        for suffix in self.ROUGH_SUFFIXES:
            if name_without_ext.lower().endswith(suffix.lower()):
                return 'ROUGH', name_without_ext[:-len(suffix)]
        
        for suffix in self.METAL_SUFFIXES:
            if name_without_ext.lower().endswith(suffix.lower()):
                return 'METAL', name_without_ext[:-len(suffix)]
        
        for suffix in self.ALBEDO_SUFFIXES:
            if name_without_ext.lower().endswith(suffix.lower()):
                return 'ALBEDO', name_without_ext[:-len(suffix)]
        
        for suffix in self.NORMAL_SUFFIXES:
            if name_without_ext.lower().endswith(suffix.lower()):
                return 'NORMAL', name_without_ext[:-len(suffix)]
        
        for suffix in self.HEIGHT_SUFFIXES:
            if name_without_ext.lower().endswith(suffix.lower()):
                return 'HEIGHT', name_without_ext[:-len(suffix)]
        
        return None, None
            
    def combine_all_textures(self):
        """Combine all texture sets and rename albedo/normal/height maps"""
        try:
            complete_sets = []
            incomplete_sets = []
            processable_sets = []
            
            # Separate complete and incomplete ORM sets
            for base_name, group in self.file_groups.items():
                has_all_orm = all([group['AO'], group['ROUGH'], group['METAL']])
                if has_all_orm:
                    complete_sets.append((base_name, group))
                    processable_sets.append((base_name, group))
                elif self.ignore_missing.get():
                    # Add to processable if ignore_missing is enabled
                    incomplete_sets.append(base_name)
                    processable_sets.append((base_name, group))
                else:
                    incomplete_sets.append(base_name)
            
            if not processable_sets:
                messagebox.showwarning("No Sets to Process", 
                    "No texture sets found to process.")
                return
            
            # Warn about incomplete sets if not ignoring
            if incomplete_sets and not self.ignore_missing.get():
                response = messagebox.askyesno("Incomplete Sets Detected",
                    f"Found {len(incomplete_sets)} incomplete ORM set(s):\n" +
                    "\n".join(incomplete_sets[:5]) +
                    ("\n..." if len(incomplete_sets) > 5 else "") +
                    f"\n\nContinue with {len(complete_sets)} complete set(s)?")
                if not response:
                    return
            
            # Process all sets
            orm_success = 0
            orm_partial = 0
            albedo_renamed = 0
            normal_renamed = 0
            height_renamed = 0
            error_count = 0
            errors = []
            
            self.status_label.config(text=f"Processing 0/{len(processable_sets)}...")
            self.root.update()
            
            for idx, (base_name, group) in enumerate(processable_sets, 1):
                try:
                    # Determine output directory (create Converted subfolder)
                    source_file = None
                    for file_type in ['AO', 'ROUGH', 'METAL', 'ALBEDO', 'NORMAL', 'HEIGHT']:
                        if group[file_type]:
                            source_file = group[file_type]
                            break
                    
                    if not source_file:
                        continue
                    
                    source_dir = os.path.dirname(source_file)
                    output_dir = os.path.join(source_dir, "Converted")
                    
                    # Create Converted folder if it doesn't exist
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Process ORM combining
                    if all([group['AO'], group['ROUGH'], group['METAL']]):
                        # Complete ORM set
                        ao_img = Image.open(group['AO']).convert('RGB')
                        rough_img = Image.open(group['ROUGH']).convert('RGB')
                        metal_img = Image.open(group['METAL']).convert('RGB')
                        
                        # Check if all images have the same size
                        if not (ao_img.size == rough_img.size == metal_img.size):
                            errors.append(f"{base_name}: Size mismatch")
                            error_count += 1
                        else:
                            # Extract red channels
                            ao_channel = ao_img.split()[0]
                            rough_channel = rough_img.split()[0]
                            metal_channel = metal_img.split()[0]
                            
                            # Combine into RGB (ORM)
                            orm_img = Image.merge('RGB', (ao_channel, rough_channel, metal_channel))
                            output_path = os.path.join(output_dir, f"{base_name}_ORM.png")
                            orm_img.save(output_path, 'PNG')
                            orm_success += 1
                    elif self.ignore_missing.get():
                        # Partial ORM with missing channels (fill with black)
                        channels = [None, None, None]
                        size = None
                        
                        if group['AO']:
                            ao_img = Image.open(group['AO']).convert('RGB')
                            channels[0] = ao_img.split()[0]
                            size = channels[0].size
                        
                        if group['ROUGH']:
                            rough_img = Image.open(group['ROUGH']).convert('RGB')
                            channels[1] = rough_img.split()[0]
                            if not size:
                                size = channels[1].size
                        
                        if group['METAL']:
                            metal_img = Image.open(group['METAL']).convert('RGB')
                            channels[2] = metal_img.split()[0]
                            if not size:
                                size = channels[2].size
                        
                        # Fill missing channels with black
                        if size:
                            for i in range(3):
                                if channels[i] is None:
                                    channels[i] = Image.new('L', size, 0)
                            
                            orm_img = Image.merge('RGB', tuple(channels))
                            output_path = os.path.join(output_dir, f"{base_name}_ORM.png")
                            orm_img.save(output_path, 'PNG')
                            orm_partial += 1
                    
                    # Rename Albedo if present
                    if group['ALBEDO']:
                        try:
                            ext = os.path.splitext(group['ALBEDO'])[1]
                            new_path = os.path.join(output_dir, f"{base_name}_BC{ext}")
                            shutil.copy2(group['ALBEDO'], new_path)
                            albedo_renamed += 1
                        except Exception as e:
                            errors.append(f"{base_name} Albedo: {str(e)}")
                            error_count += 1
                    
                    # Rename Normal if present
                    if group['NORMAL']:
                        try:
                            ext = os.path.splitext(group['NORMAL'])[1]
                            new_path = os.path.join(output_dir, f"{base_name}_N{ext}")
                            shutil.copy2(group['NORMAL'], new_path)
                            normal_renamed += 1
                        except Exception as e:
                            errors.append(f"{base_name} Normal: {str(e)}")
                            error_count += 1
                    
                    # Rename Height if present
                    if group['HEIGHT']:
                        try:
                            ext = os.path.splitext(group['HEIGHT'])[1]
                            new_path = os.path.join(output_dir, f"{base_name}_D{ext}")
                            shutil.copy2(group['HEIGHT'], new_path)
                            height_renamed += 1
                        except Exception as e:
                            errors.append(f"{base_name} Height: {str(e)}")
                            error_count += 1
                    
                    # Update status
                    self.status_label.config(text=f"Processing {idx}/{len(processable_sets)}...")
                    self.root.update()
                    
                except Exception as e:
                    errors.append(f"{base_name}: {str(e)}")
                    error_count += 1
            
            # Show results
            result_message = f"Processing complete!\n\n"
            result_message += f"✓ Created {orm_success} complete ORM texture(s)\n"
            if orm_partial > 0:
                result_message += f"✓ Created {orm_partial} partial ORM(s) with missing channels\n"
            if albedo_renamed > 0:
                result_message += f"✓ Renamed {albedo_renamed} Albedo map(s) to _BC\n"
            if normal_renamed > 0:
                result_message += f"✓ Renamed {normal_renamed} Normal map(s) to _N\n"
            if height_renamed > 0:
                result_message += f"✓ Renamed {height_renamed} Height map(s) to _D\n"
            result_message += f"\n📁 All files saved to 'Converted' subfolder(s)\n"
            
            if error_count > 0:
                result_message += f"\n⚠ {error_count} error(s) occurred:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    result_message += f"\n... and {len(errors) - 10} more"
                messagebox.showwarning("Batch Complete with Errors", result_message)
            else:
                messagebox.showinfo("Success!", result_message)
            
            status_text = f"Complete! ORM:{orm_success}"
            if orm_partial > 0:
                status_text += f"(+{orm_partial} partial)"
            status_text += f", Albedo:{albedo_renamed}, Normal:{normal_renamed}, Height:{height_renamed}, Errors:{error_count}"
            self.status_label.config(text=status_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Batch processing failed:\n{str(e)}")
            self.status_label.config(text="Error occurred during processing.")
def main():
    root = TkinterDnD.Tk()
    app = ORMCombiner(root)
    root.mainloop()

if __name__ == "__main__":
    main()
