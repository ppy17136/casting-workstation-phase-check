using System.Reflection;
using System.Text.Json;

namespace SolidWorksBridge;

internal static class Program
{
    private const int SwDocPart = 1;
    private const int SwDocAssembly = 2;
    private const int SwDocDrawing = 3;
    private const int SwOpenDocOptionsSilent = 1;
    private const int SwSaveAsOptionsSilent = 1;

    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            WriteJson(new
            {
                ok = false,
                error = "missing_command",
                supported_commands = new[] { "ping", "info", "export" }
            });
            return 1;
        }

        try
        {
            return args[0].ToLowerInvariant() switch
            {
                "ping" => Ping(),
                "info" => Info(),
                "export" => Export(args),
                _ => Unsupported(args[0]),
            };
        }
        catch (Exception ex)
        {
            WriteJson(new
            {
                ok = false,
                error = "unhandled_exception",
                message = ex.Message,
                detail = ex.ToString()
            });
            return 99;
        }
    }

    private static int Ping()
    {
        WriteJson(new
        {
            ok = true,
            bridge = "solidworks",
            version = "0.2.0"
        });
        return 0;
    }

    private static int Info()
    {
        var installedPath = FindSolidWorksPath();
        WriteJson(new
        {
            ok = true,
            solidworks_found = installedPath is not null,
            solidworks_path = installedPath ?? string.Empty,
            com_available = CanConnectCom()
        });
        return 0;
    }

    private static int Export(string[] args)
    {
        var inputPath = GetOption(args, "--input");
        var outputPath = GetOption(args, "--output");
        var format = GetOption(args, "--format");

        if (string.IsNullOrWhiteSpace(inputPath) || string.IsNullOrWhiteSpace(outputPath) || string.IsNullOrWhiteSpace(format))
        {
            WriteJson(new
            {
                ok = false,
                error = "missing_required_options",
                required = new[] { "--input", "--output", "--format" }
            });
            return 2;
        }

        if (!File.Exists(inputPath))
        {
            WriteJson(new
            {
                ok = false,
                error = "input_not_found",
                input = inputPath
            });
            return 3;
        }

        var targetDirectory = Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrWhiteSpace(targetDirectory))
        {
            Directory.CreateDirectory(targetDirectory);
        }

        object? swApp = null;
        object? model = null;
        try
        {
            swApp = ConnectSolidWorks();
            model = OpenDocument(swApp, inputPath);
            SaveDocument(model, outputPath);

            WriteJson(new
            {
                ok = true,
                input = inputPath,
                output = outputPath,
                format = format,
                exists = File.Exists(outputPath)
            });
            return 0;
        }
        catch (Exception ex)
        {
            WriteJson(new
            {
                ok = false,
                error = "export_failed",
                input = inputPath,
                output = outputPath,
                format = format,
                message = ex.Message
            });
            return 4;
        }
        finally
        {
            try
            {
                if (swApp is not null && model is not null)
                {
                    var title = InvokeMember(model, "GetTitle", BindingFlags.InvokeMethod, Array.Empty<object?>())?.ToString();
                    if (!string.IsNullOrWhiteSpace(title))
                    {
                        InvokeMember(swApp, "CloseDoc", BindingFlags.InvokeMethod, new object?[] { title });
                    }
                }
            }
            catch
            {
                // Ignore cleanup failures
            }
        }
    }

    private static object ConnectSolidWorks()
    {
        var type = Type.GetTypeFromProgID("SldWorks.Application");
        if (type is null)
        {
            throw new InvalidOperationException("Cannot locate SolidWorks COM ProgID.");
        }

        var app = Activator.CreateInstance(type);
        if (app is null)
        {
            throw new InvalidOperationException("Failed to create SolidWorks COM instance.");
        }

        InvokeMember(app, "Visible", BindingFlags.SetProperty, new object?[] { false });
        InvokeMember(app, "UserControl", BindingFlags.SetProperty, new object?[] { false });
        return app;
    }

    private static object OpenDocument(object swApp, string inputPath)
    {
        var extension = Path.GetExtension(inputPath).ToLowerInvariant();
        var documentType = extension switch
        {
            ".sldprt" => SwDocPart,
            ".sldasm" => SwDocAssembly,
            ".slddrw" => SwDocDrawing,
            _ => throw new InvalidOperationException($"Unsupported SolidWorks file type: {extension}")
        };

        object?[] openArgs = { inputPath, documentType, SwOpenDocOptionsSilent, "", 0, 0 };
        var model = InvokeMember(swApp, "OpenDoc6", BindingFlags.InvokeMethod, openArgs);
        if (model is null)
        {
            throw new InvalidOperationException("SolidWorks failed to open the input document.");
        }
        return model;
    }

    private static void SaveDocument(object model, string outputPath)
    {
        var extensionObj = InvokeMember(model, "Extension", BindingFlags.GetProperty, Array.Empty<object?>());
        if (extensionObj is null)
        {
            throw new InvalidOperationException("Failed to access SolidWorks ModelDocExtension.");
        }

        object?[] saveArgs = { outputPath, 0, SwSaveAsOptionsSilent, null, 0, 0 };
        var result = InvokeMember(extensionObj, "SaveAs", BindingFlags.InvokeMethod, saveArgs);

        var success = result is bool b && b;
        if (!success || !File.Exists(outputPath))
        {
            throw new InvalidOperationException("SolidWorks reported export failure or output file was not created.");
        }
    }

    private static object? InvokeMember(object target, string memberName, BindingFlags flags, object?[] args)
    {
        return target
            .GetType()
            .InvokeMember(memberName, flags, binder: null, target, args);
    }

    private static string? GetOption(string[] args, string optionName)
    {
        var index = Array.IndexOf(args, optionName);
        if (index < 0 || index + 1 >= args.Length)
        {
            return null;
        }

        return args[index + 1];
    }

    private static string? FindSolidWorksPath()
    {
        var candidates = new[]
        {
            @"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
            @"C:\Program Files (x86)\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
            @"E:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
            @"E:\Program Files (x86)\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe"
        };

        return candidates.FirstOrDefault(File.Exists);
    }

    private static bool CanConnectCom()
    {
        try
        {
            var type = Type.GetTypeFromProgID("SldWorks.Application");
            return type is not null;
        }
        catch
        {
            return false;
        }
    }

    private static int Unsupported(string command)
    {
        WriteJson(new
        {
            ok = false,
            error = "unsupported_command",
            command
        });
        return 5;
    }

    private static void WriteJson(object payload)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        Console.WriteLine(JsonSerializer.Serialize(payload));
    }
}
