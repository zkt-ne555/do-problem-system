import os
import zipfile

def main():
    # 定义要排除的文件和文件夹黑名单
    exclude_dirs = {
        'frontend/node_modules',
        'frontend/dist',
        'venv',
        'env',
        '__pycache__',
        'dist',
        'build',
        '.git',
        '.npm-cache'
    }
    
    exclude_files = {
        '.env',
        'pack_source.py',
        '.DS_Store'
    }
    
    exclude_patterns = ('*.spec',)
    
    # 输出ZIP文件名
    zip_filename = 'SmartExamSystem_Source.zip'
    
    # 获取当前脚本所在目录（项目根目录）
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 删除已存在的ZIP文件
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
        print(f"已删除旧的 {zip_filename}")
    
    # 创建ZIP文件
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        total_files = 0
        
        # 遍历目录
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 计算相对路径
            rel_path = os.path.relpath(dirpath, root_dir)
            
            # 跳过黑名单目录（修改dirnames会影响后续遍历）
            dirnames[:] = [d for d in dirnames if os.path.join(rel_path, d) not in exclude_dirs]
            
            # 如果是根目录且rel_path为.，设置为空字符串
            if rel_path == '.':
                rel_path = ''
            
            # 处理文件
            for filename in filenames:
                # 跳过黑名单文件
                if filename in exclude_files:
                    continue
                
                # 检查文件名模式匹配
                skip = False
                for pattern in exclude_patterns:
                    if filename.endswith(pattern[1:]):  # 去掉星号
                        skip = True
                        break
                if skip:
                    continue
                
                # 构建文件完整路径和归档路径
                file_path = os.path.join(dirpath, filename)
                arcname = os.path.join(rel_path, filename) if rel_path else filename
                
                # 添加到ZIP
                zipf.write(file_path, arcname)
                total_files += 1
                print(f"正在打包: {arcname}")
        
        # 打包完成
        zip_size = os.path.getsize(zip_filename)
        print(f"\n{'='*50}")
        print(f"打包完成！共打包 {total_files} 个文件")
        print(f"输出文件: {zip_filename}")
        print(f"文件大小: {zip_size / 1024:.2f} KB ({zip_size:,} 字节)")
        print(f"{'='*50}")

if __name__ == '__main__':
    main()
