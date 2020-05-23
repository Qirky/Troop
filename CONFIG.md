# Troop Interpreter Configuration

Troop has seen some updates to its configuration to communicate with your live coding language, such as FoxDot and Tidal Cycles. Instead of the `boot.txt` file to point an interpreter to the location of a boot-file, Troop now uses `boot.json` to configure a language's executable path *and* bootfile. Let's look at how this affects Tidal users as an example:

## Editing paths

TidalCycles, and it's host language Haskell, can be installed in different ways and use different executables to startup using the Glasgow Haskell Compiler but is most commonly run using the `ghci` executable. By default, TidalCycles will try and start using this file by default but not all instances of Tidal are run using it. For example, some users will have used 'stack' to install Tidal and will have to run it using `stach ghci`. Previously Troop included an extra drop-down option for the client for Tidal users using stack but this *no longer exists*. Instead, users now need edit the `src/conf/boot.json` file to point Tidal in the direction of `stack ghci`. This is what the file looks like by default:

```json
{
  "foxdot": {
      "path": "",
      "bootfile": ""
  },
  "tidalcycles": {
      "path": "",
      "bootfile": ""
  }
}
```

If an empty path/bootfile is set, Troop will use the default (`ghci` for Tidal in this instance). To use `stack ghci` simply change the value for "path" under "tidalcycles" like so:


```json
{
  "foxdot": {
      "path": "",
      "bootfile": ""
  },
  "tidalcycles": {
      "path": "stack ghci",
      "bootfile": ""
  }
}
```

After you save the file, Troop will use the new executable when starting up TidalCycles. User who use the `ghc` executable for Haskell can change the value as needed too.

## Editing bootfile

The bootfile parameter mainly relates to TidalCycles but can also be used with FoxDot, but we will discuss Tidal config mainly here. Tidal requires that a `BootTidal.hs` file is run by the Haskell compile to load the necessary libraries and set any required values - without it, Tidal will not run. Troop uses the `ghc-pkg` application to find where this is stored - usually in the Tidal installation folder. You may wish to override this for a number of reasons:

- The `ghc-pkg` file cannot find the boot file
- The `ghc-pkg` is not installed/not on your path
- You have a customer boot file you wish to run (also the case for FoxDot)

You can manually set the path to your boot file in `src/conf/boot.json` by setting the "bootfile" parameter under your desired language. So if we had a custom Tidal bootfile in a directory called `/home/ryan/dev/` called `custom.hs` I would change my `boot.json` file to the following:

```json
{
  "foxdot": {
      "path": "",
      "bootfile": ""
  },
  "tidalcycles": {
      "path": "",
      "bootfile": "/home/ryan/dev/custom.hs"
  }
}
```

Save the file and start Troop in Tidal mode to boot with your custom file!
